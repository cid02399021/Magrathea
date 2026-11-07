#include "tp_diagnostics.h"

#include <algorithm>
#include <cerrno>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <limits>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "EOSlist.h"
#include "hydro.h"
#include "tp_profile.h"

namespace {

// JSON number formatting: always max_digits10, finite required.
std::string format_double(double v) {
    if (!std::isfinite(v)) throw std::runtime_error("Non-finite double in diagnostics");
    std::ostringstream oss;
    oss << std::setprecision(std::numeric_limits<double>::max_digits10) << v;
    return oss.str();
}

// Write JSON string with escaping (handles fixed IDs if they contain special characters).
void write_json_string(std::ostream& os, const std::string& s) {
    os << '\"';
    for (char c : s) {
        switch (c) {
            case '\\': os << "\\\\"; break;
            case '\"': os << "\\\""; break;
            case '\n': os << "\\n"; break;
            case '\r': os << "\\r"; break;
            case '\t': os << "\\t"; break;
            default: os << c;
        }
    }
    os << '\"';
}

struct GasRow {
    double mass_g;
    double pressure_cgs;
    double temperature_K;
    double density_g_cm3;
};

// Compute actual gas rows using component mass interval boundaries and EOS pointers.
// selector: "gas_fixed_mu2" (legacy) -> Gas pointer, "gas_hhe_prescribed" -> Gas_hhe pointer.
std::vector<GasRow> collect_gas_rows(hydro& model, const std::string& selector) {
    const TPDiagnostics& diag = model.tp_diagnostics();
    const double gas_base_mass = diag.gas_base_mass;
    const double total_mass = model.totalM();
    const double eps = 64.0 * std::numeric_limits<double>::epsilon();

    EOS* gas_eos = nullptr;
    if (selector == "gas_fixed_mu2") {
        gas_eos = Gas;
    } else if (selector == "gas_hhe_prescribed") {
        gas_eos = Gas_hhe;
    } else {
        throw std::runtime_error("Unknown EOS selector in collect_gas_rows");
    }
    if (gas_eos == nullptr) {
        throw std::runtime_error("Gas EOS pointer is null for selector " + selector);
    }

    // Identify boundaries with tolerance.
    std::vector<int> layer_indices;
    const int size = model.getsize();
    if (size <= 0) throw std::runtime_error("hydro model has no layers");

    // Find candidate gas-side boundary: first layer whose M is within eps of gas_base_mass
    // and whose phase is Gas. Also ensure it is not a duplicated solid-side boundary.
    int gas_base_idx = -1;
    for (int i = 0; i < size; ++i) {
        const double m = model.getM(i);
        if (std::abs(m - gas_base_mass) <= eps * std::max(1.0, std::abs(gas_base_mass))) {
            const EOS* phase = model.getphase(i);
            if (phase == gas_eos) {
                gas_base_idx = i;
                break;
            }
        }
    }
    if (gas_base_idx < 0) throw std::runtime_error("gas_base_mass not found at Gas phase boundary");

    // Collect rows from gas_base_idx up to last layer inclusive.
    std::vector<GasRow> rows;
    for (int i = gas_base_idx; i < size; ++i) {
        const double mass = model.getM(i);
        // Validate mass range with tolerance relative to magnitudes.
        if (!(mass >= gas_base_mass - eps * std::max(1.0, std::abs(gas_base_mass)) &&
              mass <= total_mass + eps * std::max(1.0, std::abs(total_mass)))) {
            throw std::runtime_error("gas row mass outside valid interval");
        }
        if (model.getphase(i) != gas_eos) {
            // Allow skipped duplicated SOLID-side boundary row only if mass is within roundoff of gas_base_mass (zero-jump interface).
            if (std::abs(mass - gas_base_mass) <= eps * std::max(1.0, std::abs(gas_base_mass))) {
                continue;
            } else {
                throw std::runtime_error("Non-Gas phase inside gas mass interval");
            }
        }
        // Exclude any mass beyond total mass (should not happen).
        if (mass > total_mass + eps * std::max(1.0, std::abs(total_mass))) {
            throw std::runtime_error("gas row mass exceeds total mass");
        }

        const double p = model.getP(i);
        const double t = model.getT(i);
        const double rho = model.getrho(i);
        if (!(std::isfinite(mass) && std::isfinite(p) && std::isfinite(t) && std::isfinite(rho))) {
            throw std::runtime_error("Non-finite value in gas row");
        }
        if (p <= 0.0 || rho <= 0.0) {
            throw std::runtime_error("Non-positive pressure or density in gas row");
        }

        GasRow row;
        row.mass_g = mass;
        row.pressure_cgs = p;
        row.temperature_K = t;
        row.density_g_cm3 = rho;
        rows.push_back(row);
    }

    if (rows.empty()) throw std::runtime_error("No gas rows collected");
    return rows;
}

// Validate all required diagnostics and model state.
void validate_inputs(hydro& model, double surfaceP_cgs, double surfaceT_K) {
    const TPDiagnostics& diag = model.tp_diagnostics();
    if (!diag.enabled) throw std::runtime_error("TPD diagnostics not enabled");
    if (model.getstatus() != 0) throw std::runtime_error("hydro ode_status != 0");
    if (!diag.error.empty()) throw std::runtime_error("TPD error string non-empty");
    if (diag.corrected_fit) throw std::runtime_error("corrected_fit is true");

    if (!(std::isfinite(surfaceP_cgs) && std::isfinite(surfaceT_K))) {
        throw std::runtime_error("surface pressure/temperature not finite");
    }
    if (surfaceP_cgs <= 0.0) throw std::runtime_error("surface pressure must be positive");

    // Check required TPD fields are finite.
    const double fields[] = {
        diag.gas_pressure_min,
        diag.gas_pressure_max,
        diag.accepted_gas_pressure_max,
        diag.gas_base_pressure,
        diag.gas_base_temperature,
        diag.gas_base_mass,
        diag.fit_mass,
        diag.max_pre_projection_relative,
        diag.max_effective_relative,
        diag.max_density_relative,
        diag.fit_Ri, diag.fit_Ro,
        diag.fit_Pi, diag.fit_Po,
        diag.fit_Ti, diag.fit_To,
        diag.max_knot_pressure_projection_relative
    };
    for (double v : fields) {
        if (!std::isfinite(v)) throw std::runtime_error("Non-finite TPD field");
    }

    if (diag.gas_pressure_min <= 0.0 || diag.gas_pressure_max <= 0.0 ||
        diag.accepted_gas_pressure_max <= 0.0 || diag.gas_base_pressure <= 0.0 ||
        diag.gas_base_mass <= 0.0 || diag.fit_mass <= 0.0) {
        throw std::runtime_error("Physically positive field non-positive");
    }

    if (diag.max_pre_projection_relative < 0.0 ||
        diag.max_effective_relative < 0.0 ||
        diag.max_density_relative < 0.0 ||
        diag.max_knot_pressure_projection_relative < 0.0) {
        throw std::runtime_error("Non-negative relative field is negative");
    }
}

// Emit layer rows for schema version 2.
// Each accepted model row is an object with fields:
// mass_g, radius_cm, pressure_cgs, temperature_K, density_g_cm3,
// actual_eos_id, thermal_code, table_domain_contains,
// reevaluated_density_g_cm3, expected_eos_by_slot array of 4 objects.
void emit_layer_rows(std::ostream& json, hydro& model, const std::string& selector) {
    json << "[";
    bool first_row = true;
    for (int i = 0; i < model.getsize(); ++i) {
        const double mass = model.getM(i);
        const EOS* phase = model.getphase(i);
        if (phase == nullptr) throw std::runtime_error("Null phase in emit_layer_rows");

        const double p = model.getP(i);
        const double t = model.getT(i);
        const double rho_stored = model.getrho(i);
        const double r = model.getR(i);
        if (!(std::isfinite(mass) && std::isfinite(p) && std::isfinite(t) && std::isfinite(rho_stored) && std::isfinite(r))) {
            throw std::runtime_error("Non-finite value in layer row");
        }
        if (p <= 0.0 || t <= 0.0 || rho_stored <= 0.0 || r < 0.0) {
            throw std::runtime_error("Non-positive pressure/temperature/density or negative radius in layer row");
        }

        // Reevaluate density via non-const EOS pointer.
        EOS* mutable_phase = const_cast<EOS*>(phase);
        if (!mutable_phase->table_domain_contains(p, t)) {
            throw std::runtime_error("Actual EOS out of numerical domain in layer row");
        }
        const double rho_reeval = mutable_phase->density(p, t, -1);
        if (!std::isfinite(rho_reeval) || rho_reeval <= 0.0) {
            throw std::runtime_error("Reevaluated density non-finite or non-positive");
        }

        if (!first_row) json << ",";
        first_row = false;
        json << "{";
        json << "\"mass_g\":" << format_double(mass) << ",";
        json << "\"radius_cm\":" << format_double(r) << ",";
        json << "\"pressure_cgs\":" << format_double(p) << ",";
        json << "\"temperature_K\":" << format_double(t) << ",";
        json << "\"density_g_cm3\":" << format_double(rho_stored) << ",";
        json << "\"actual_eos_id\":"; write_json_string(json, phase->audit_id()); json << ",";
        json << "\"thermal_code\":" << phase->thermal_code() << ",";
        json << "\"table_domain_contains\":" << (phase->table_domain_contains(p, t) ? "true" : "false") << ",";
        json << "\"reevaluated_density_g_cm3\":" << format_double(rho_reeval) << ",";

        // expected_eos_by_slot: array of 4 objects.
        const std::vector<double>& M_Comp = model.component_masses();
        if (M_Comp.size() != 4) {
            throw std::runtime_error("Expected 4 component masses for schema2 layer rows");
        }
        json << "\"expected_eos_by_slot\":[";
        for (size_t slot = 0; slot < 4; ++slot) {
            if (slot > 0) json << ",";
            json << "{";
            json << "\"slot\":" << slot << ",";
            json << "\"mass_ME\":" << format_double(M_Comp[slot]) << ",";
            if (M_Comp[slot] <= 0.0) {
                // Zero mass: emit empty exact ID and empty nearby array, do NOT call find_phase.
                json << "\"exact_eos_id\":\"\",";
                json << "\"nearby_eos_ids\":[]";
            } else {
                // Positive slot: call component_phase at same P/T and 8 neighbors.
                EOS* comp_phase = model.component_phase(static_cast<int>(slot), p, t);
                if (comp_phase == nullptr) {
                    throw std::runtime_error("component_phase returned null for positive slot");
                }
                json << "\"exact_eos_id\":"; write_json_string(json, comp_phase->audit_id()); json << ",";

                std::set<std::string> nearby_ids;
                // Neighbors: P*(1 +/- 1e-7), T*(1 +/- 1e-7), and combinations (8 total).
                const double p_factor[3] = {1.0 - 1e-7, 1.0, 1.0 + 1e-7};
                const double t_factor[3] = {1.0 - 1e-7, 1.0, 1.0 + 1e-7};
                for (int pi = 0; pi < 3; ++pi) {
                    for (int ti = 0; ti < 3; ++ti) {
                        if (pi == 1 && ti == 1) continue; // skip exact center (already exact_eos_id)
                        const double neighbor_P = p * p_factor[pi];
                        const double neighbor_T = t * t_factor[ti];
                        if (neighbor_P <= 0.0 || neighbor_T <= 0.0) {
                            throw std::runtime_error("Non-positive neighbor P/T in component_phase");
                        }
                        EOS* neighbor_phase = model.component_phase(static_cast<int>(slot), neighbor_P, neighbor_T);
                        if (neighbor_phase != nullptr) {
                            nearby_ids.insert(neighbor_phase->audit_id());
                        }
                    }
                }
                // Remove exact ID if present (just in case).
                nearby_ids.erase(comp_phase->audit_id());

                json << "\"nearby_eos_ids\":[";
                bool first_nearby = true;
                for (const std::string& id : nearby_ids) {
                    if (!first_nearby) json << ",";
                    first_nearby = false;
                    write_json_string(json, id);
                }
                json << "]";
            }
            json << "}";
        }
        json << "]";
        json << "}";
    }
    json << "]";
    if (first_row) {
        throw std::runtime_error("No layer rows generated for schema2");
    }
}

// Build JSON string in memory.
std::string build_json(hydro& model, const TPProfile& tp,
                       double surfaceP_cgs, double surfaceT_K,
                       const std::vector<GasRow>& gas_rows,
                       const std::string& selector) {
    const TPDiagnostics& diag = model.tp_diagnostics();
    std::ostringstream json;
    json << std::setprecision(std::numeric_limits<double>::max_digits10);

    const double profile_min_p = tp.min_pressure_cgs();
    const double profile_max_p = tp.max_pressure_cgs();
    if (!(std::isfinite(profile_min_p) && std::isfinite(profile_max_p)) ||
        profile_min_p <= 0.0 || profile_max_p <= 0.0 || profile_min_p > profile_max_p) {
        throw std::runtime_error("Invalid TP profile pressure range");
    }

    if (gas_rows.empty()) {
        throw std::runtime_error("No gas rows collected");
    }

    double max_effective_rel = 0.0;
    double max_density_rel = 0.0;

    EOS* gas_eos = nullptr;
    if (selector == "gas_fixed_mu2") {
        gas_eos = Gas;
    } else if (selector == "gas_hhe_prescribed") {
        gas_eos = Gas_hhe;
    } else {
        throw std::runtime_error("Unknown EOS selector in build_json");
    }
    if (gas_eos == nullptr) {
        throw std::runtime_error("Gas EOS pointer is null");
    }

    for (const GasRow& row : gas_rows) {
        const double expected_T = tp.at_cgs(row.pressure_cgs).temperature_K;
        if (!std::isfinite(expected_T) || expected_T <= 0.0) {
            throw std::runtime_error("Invalid expected temperature in gas row");
        }

        const double expected_rho = gas_eos->density(row.pressure_cgs, expected_T, -1);
        if (!std::isfinite(expected_rho) || expected_rho <= 0.0) {
            throw std::runtime_error("Invalid expected density in gas row");
        }
        if (!(row.density_g_cm3 > 0.0) || !std::isfinite(row.density_g_cm3)) {
            throw std::runtime_error("Stored density non-positive or non-finite");
        }

        const double eff_rel = std::abs(row.temperature_K - expected_T) / std::max(1.0, std::abs(expected_T));
        if (eff_rel > max_effective_rel) max_effective_rel = eff_rel;

        const double den_rel = std::abs(expected_rho - row.density_g_cm3) / expected_rho;
        if (den_rel > max_density_rel) max_density_rel = den_rel;
    }

    const double fit_Ri = diag.fit_Ri;
    const double fit_Ro = diag.fit_Ro;
    const double fit_Pi = diag.fit_Pi;
    const double fit_Po = diag.fit_Po;
    const double fit_Ti = diag.fit_Ti;
    const double fit_To = diag.fit_To;
    const double denom_R = fit_Ri + fit_Ro;
    const double denom_P = fit_Pi + fit_Po;
    const double denom_T = fit_Ti + fit_To;
    if (denom_R == 0.0 || !std::isfinite(denom_R) ||
        denom_P == 0.0 || !std::isfinite(denom_P) ||
        denom_T == 0.0 || !std::isfinite(denom_T)) {
        throw std::runtime_error("Zero or non-finite fit residual denominator");
    }

    const double total_mass = model.totalM();
    const double total_radius = model.totalR();
    if (!(total_mass > 0.0) || !(total_radius > 0.0) ||
        !std::isfinite(total_mass) || !std::isfinite(total_radius)) {
        throw std::runtime_error("Invalid total mass or radius");
    }
    if (!(surfaceT_K > 0.0) || !std::isfinite(surfaceT_K)) {
        throw std::runtime_error("Invalid surface temperature");
    }
    if (!(diag.gas_base_temperature > 0.0) || !std::isfinite(diag.gas_base_temperature)) {
        throw std::runtime_error("Invalid gas base temperature");
    }

    if (selector == "gas_hhe_prescribed") {
        // Strict table audit must be enabled for new selector.
        if (!EOS::strict_table_audit()) {
            throw std::runtime_error("Strict table audit must be enabled for gas_hhe_prescribed selector");
        }
        if (model.component_masses().size() != 4) {
            throw std::runtime_error("Expected 4 component masses for gas_hhe_prescribed");
        }
    }

    auto emit_double = [&json](const char* name, double value) {
        json << "\"" << name << "\":" << format_double(value) << ",";
    };

    json << "{";
    if (selector == "gas_hhe_prescribed") {
        json << "\"schema_version\":2,";
    } else {
        json << "\"schema_version\":1,";
    }
    json << "\"status\":\"success\",";
    if (selector == "gas_hhe_prescribed") {
        json << "\"eos_selector\":\"gas_hhe_prescribed\",";
        json << "\"helium_mass_fraction\":0.275,";
        // Do NOT emit fake mmol/n fields.
    } else {
        json << "\"eos_selector\":\"gas_fixed_mu2\",";
        json << "\"mmol\":2,";
        json << "\"n\":2,";
    }
    json << "\"pressure_unit\":\"dyn/cm2\",";
    json << "\"temperature_unit\":\"K\",";
    json << "\"mass_unit\":\"g\",";
    emit_double("outer_pressure_cgs", surfaceP_cgs);
    emit_double("outer_temperature_K", surfaceT_K);
    emit_double("profile_min_pressure_cgs", profile_min_p);
    emit_double("profile_max_pressure_cgs", profile_max_p);
    emit_double("gas_pressure_min", diag.gas_pressure_min);
    emit_double("gas_pressure_max", diag.gas_pressure_max);
    emit_double("accepted_gas_pressure_max", diag.accepted_gas_pressure_max);
    emit_double("gas_base_pressure", diag.gas_base_pressure);
    emit_double("gas_base_temperature", diag.gas_base_temperature);
    emit_double("gas_base_mass", diag.gas_base_mass);
    emit_double("fit_mass", diag.fit_mass);
    emit_double("max_pre_projection_relative", diag.max_pre_projection_relative);
    emit_double("max_effective_relative", max_effective_rel);
    emit_double("max_density_relative", max_density_rel);
    emit_double("max_knot_pressure_projection_relative", diag.max_knot_pressure_projection_relative);
    json << "\"knot_snaps\":" << diag.knot_snaps << ",";
    json << "\"ode_status\":" << model.getstatus() << ",";
    json << "\"corrected_fit\":" << (diag.corrected_fit ? "true" : "false") << ",";
    emit_double("total_mass_g", total_mass);
    emit_double("total_radius_cm", total_radius);

    // Schema 2 additional counters and layer rows.
    if (selector == "gas_hhe_prescribed") {
        json << "\"strict_table_audit\":" << (EOS::strict_table_audit() ? "true" : "false") << ",";
        json << "\"layer_rows\":";
        emit_layer_rows(json, model, selector);
        json << ",";
        json << "\"accepted_model_rows\":" << model.getsize() << ",";
        json << "\"rejected_table_queries\":" << EOS::rejected_table_queries() << ",";
        json << "\"density_audit_counts\":{";
        const std::map<std::string, unsigned long long> density_counts = EOS::density_audit_counts();
        bool first_density = true;
        for (const auto& entry : density_counts) {
            if (!first_density) json << ",";
            first_density = false;
            write_json_string(json, entry.first);
            json << ":" << entry.second;
        }
        json << "},";
        json << "\"gradient_audit_counts\":{";
        const std::map<std::string, unsigned long long> gradient_counts = EOS::gradient_audit_counts();
        bool first_gradient = true;
        for (const auto& entry : gradient_counts) {
            if (!first_gradient) json << ",";
            first_gradient = false;
            write_json_string(json, entry.first);
            json << ":" << entry.second;
        }
        json << "},";
    }

    json << "\"fit_raw\":{";
    emit_double("Ri", fit_Ri);
    emit_double("Ro", fit_Ro);
    emit_double("Pi", fit_Pi);
    emit_double("Po", fit_Po);
    emit_double("Ti", fit_Ti);
    emit_double("To", fit_To);
    json.seekp(-1, json.cur);
    json << "},";

    json << "\"fit_residual\":{";
    emit_double("radius", (fit_Ri - fit_Ro) / denom_R);
    emit_double("pressure", (fit_Pi - fit_Po) / denom_P);
    emit_double("temperature", (fit_Ti - fit_To) / denom_T);
    json.seekp(-1, json.cur);
    json << "},";

    // Note: For schema2, layer_rows already emitted. For schema1, gas_rows will be emitted here.
    json << "\"gas_rows\":[";
    for (size_t i = 0; i < gas_rows.size(); ++i) {
        const GasRow& row = gas_rows[i];
        json << "{";
        emit_double("mass_g", row.mass_g);
        emit_double("pressure_cgs", row.pressure_cgs);
        emit_double("temperature_K", row.temperature_K);
        emit_double("density_g_cm3", row.density_g_cm3);
        json.seekp(-1, json.cur);
        json << "}";
        if (i != gas_rows.size() - 1) json << ",";
    }
    json << "]";

    json << "}";
    return json.str();
}
} // namespace

void write_tp_diagnostics(const std::string& output_file, hydro& model,
                          const TPProfile& tp, double surfaceP_cgs,
                          double surfaceT_K,
                          const std::string& selector) {
    if (selector != "gas_fixed_mu2" && selector != "gas_hhe_prescribed") {
        throw std::runtime_error("Unknown selector in write_tp_diagnostics");
    }

    // Remove prior sidecar first.
    remove_tp_sidecar(output_file);

    // Validate model and inputs.
    validate_inputs(model, surfaceP_cgs, surfaceT_K);

    // Collect gas rows.
    std::vector<GasRow> gas_rows = collect_gas_rows(model, selector);
    if (gas_rows.empty()) throw std::runtime_error("No gas rows");

    // Build JSON.
    std::string json = build_json(model, tp, surfaceP_cgs, surfaceT_K, gas_rows, selector);

    // Atomic write: write to temporary then rename.
    const std::string tmp_file = output_file + ".tp.json.tmp";
    const std::string final_file = output_file + ".tp.json";
    {
        std::ofstream out(tmp_file, std::ios::out | std::ios::trunc);
        if (!out) {
            std::remove(tmp_file.c_str());
            throw std::runtime_error("Failed to open temporary file for writing");
        }
        out << json;
        out.flush();
        if (!out.good()) {
            out.close();
            std::remove(tmp_file.c_str());
            throw std::runtime_error("Failed to write JSON to temporary file");
        }
        out.close();
        if (!out.good()) {
            std::remove(tmp_file.c_str());
            throw std::runtime_error("Failed to close temporary file");
        }
    }
    if (std::rename(tmp_file.c_str(), final_file.c_str()) != 0) {
        std::remove(tmp_file.c_str());
        throw std::runtime_error("Failed to rename temporary file to final sidecar");
    }
}

void remove_tp_sidecar(const std::string& output_file) {
    const std::string sidecar = output_file + ".tp.json";
    if (std::remove(sidecar.c_str()) != 0) {
        if (errno != ENOENT) {
            throw std::runtime_error(std::string("Failed to remove sidecar: ") + std::strerror(errno));
        }
        // ENOENT: nothing to remove, OK.
    }
}
