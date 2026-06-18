# Upstream For-Bin NMR Simulation Integration

Source repository:

```text
https://github.com/z741523420-max/NMR-simulation-of-2D-3D-projext/tree/For-Bin
```

Reference branch head inspected during integration:

```text
2536f225b74ba5748687fcc68cd96c713237604d  refs/heads/For-Bin
```

The ideal triangle workflow in this app is based on the upstream `Auto_NMR.py`
path rather than the PNG phase-map path. The current local integration is
limited to the 1D T2 workflow; it intentionally does not run the upstream
T2-T2 or D-T2 modules yet. The relevant upstream concepts copied into
`t2_agent/simulation_2d.py` are:

- ideal triangular pore construction with `pygimli.meshtools.createPolygon`;
- optional gas/bubble area handling inside a triangular pore;
- coupled large/small pore construction with a rectangular throat;
- pyGIMLi PDE stepping through `pg.solve` / `pg.solver.solve`;
- cell-volume weighted decay integration for coupled large/small pores;
- Large / Small / Total T2 component export and a T2 dashboard figure.

The app still keeps PNG phase-map support for user-uploaded red/yellow/white
images. When `geometry_mode="rule"` is used and no PNG is uploaded, the app now
runs the upstream-style ideal triangular-pore workflow directly and does not
generate `rule_geometry_phase.png` as an intermediate input.
