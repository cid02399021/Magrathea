#include "tp_profile.h"
#include <cerrno>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <vector>

// Strict numeric parser: full string must be a positive finite double.
// Returns false on any failure.
static bool parse_positive_finite_double(const std::string& s, double& out) {
    if (s.empty()) return false;
    errno = 0;
    char* endptr = nullptr;
    const char* cstr = s.c_str();
    double val = std::strtod(cstr, &endptr);
    if (errno == ERANGE) return false;
    if (endptr != cstr + s.size()) return false;
    if (!std::isfinite(val) || val <= 0.0) return false;
    out = val;
    return true;
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cerr << "Usage: tp_query PROFILE.csv P_bar [P_bar...]\n";
        return 1;
    }

    std::string profile_path = argv[1];

    // Parse all query pressures first
    std::vector<double> queries;
    for (int i = 2; i < argc; ++i) {
        double p_bar;
        if (!parse_positive_finite_double(argv[i], p_bar)) {
            std::cerr << "Invalid query pressure: " << argv[i] << "\n";
            return 1;
        }
        // Check conversion to cgs
        double p_cgs = p_bar * 1e6;
        if (!std::isfinite(p_cgs) || p_cgs <= 0.0) {
            std::cerr << "Query pressure out of range: " << argv[i] << "\n";
            return 1;
        }
        queries.push_back(p_cgs);
    }

    if (queries.empty()) {
        std::cerr << "Requires at least one query pressure.\n";
        return 1;
    }

    // Initialize directly via static load_csv within try to avoid private default ctor issue
    std::vector<TPState> results;
    try {
        TPProfile prof = TPProfile::load_csv(profile_path);
        // Evaluate all queries into vector first
        for (double p_cgs : queries) {
            TPState state = prof.at_cgs(p_cgs);
            results.push_back(state);
        }
    } catch (const std::exception& e) {
        std::cerr << "Query evaluation failed: " << e.what() << "\n";
        return 1;
    }

    // All succeeded, print JSON array
    std::cout << std::setprecision(std::numeric_limits<double>::max_digits10);
    std::cout << "[";
    for (size_t i = 0; i < results.size(); ++i) {
        if (i > 0) std::cout << ",";
        const TPState& s = results[i];
        double pressure_bar = queries[i] / 1e6;
        std::cout << "{\"pressure_bar\":" << pressure_bar
                  << ",\"temperature_K\":" << s.temperature_K
                  << ",\"dT_dP_cgs\":" << s.dT_dP_cgs << "}";
    }
    std::cout << "]\n";

    return 0;
}
