# Bundled NMR Simulation Provenance

The ideal-triangle workflow is now implemented inside this repository and is
called through `t2_agent.simulation_2d`. Public deployments do not need a
separate NMR project checkout or Git submodule.

Historical reference repository used when the bundled workflow was first
adapted:

```text
https://github.com/z741523420-max/NMR-simulation-of-2D-3D-projext/tree/For-Bin
```

Reference branch head inspected during integration:

```text
2536f225b74ba5748687fcc68cd96c713237604d  refs/heads/For-Bin
```

The bundled ideal-triangle workflow follows the `Auto_NMR.py` style rather than
the PNG phase-map path. The current implementation is limited to the 1D T2
workflow; it intentionally does not run T2-T2 or D-T2 modules yet. The relevant
concepts copied into `t2_agent/simulation_2d.py` are:

- ideal triangular pore construction with `pygimli.meshtools.createPolygon`;
- optional gas/bubble area handling inside a triangular pore;
- coupled large/small pore construction with a rectangular throat;
- pyGIMLi PDE stepping through `pg.solve` / `pg.solver.solve`;
- cell-volume weighted decay integration for coupled large/small pores;
- Large / Small / Total T2 component export and a T2 dashboard figure.

The app still keeps PNG phase-map support for user-uploaded red/yellow/white
images. When `geometry_mode="rule"` is used and no PNG is uploaded, the app now
runs the bundled ideal triangular-pore workflow directly and does not generate
`rule_geometry_phase.png` as an intermediate input.
