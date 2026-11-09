# PICASO source for TOI-732 c research

PICASO is an upstream project by Natasha Batalha and collaborators. Its source is
linked here as a Git submodule, pinned to commit
`4524b70861c5034564e65bfb71b664ea49c425b1` of
https://github.com/natashabatalha/picaso . This is not MAGRATHEA code and no
PICASO–MAGRATHEA coupling or TOI-732 c simulation is claimed.

To obtain the pinned source after cloning this repository, run
`git submodule update --init external/picaso` from the repository root.
The upstream PICASO project uses GPL-3.0; see its own LICENSE file. Its
reference/opacity datasets can be many GB and must be obtained separately using
the official installation instructions:
https://natashabatalha.github.io/picaso/installation.html .

The climate calculation needs stellar irradiation, gravity, composition,
opacities, intrinsic flux and boundary choices. A generated T(P) profile is a
model output and must be validated before passing it to MAGRATHEA.
