# Audit and Revision Notes

审核子智能体结论：有条件通过；结构完整，但需收紧 citation key、过泛化标签和证据锚点。

## 已修正

- `literature_manifest.json` 与 `literature_manifest.enriched.json` 中的 `citation_key` 已统一为唯一的 `agent_citation_key`。原始自动键保留在 `citation_key_original`。
- `BrownsteinTarr1979` 定位已改为表面弛豫/受限扩散/几何模态，不再作为正则化或 L-curve 主引用。
- `EchoTrainSimulation2021` 已限定为 CPMG/echo train/pulse sequence 采样影响，不再带 regularization / L-curve / NNLS 标签。
- T2-T2 论文的反演标签改为 `regularized_inversion` / `inverse_laplace` 语境，不再将其标为一维 L-curve 来源。
- 高频引用卡新增页码/缓存行号证据锚点：Whittall、Coates、Brownstein、Mohnke2010、EchoTrainSimulation2021。
- 场景从 15 个扩展到 21 个，新增 L-curve 不稳定、Gaussian 过拟合、表面弛豫率敏感、网格/边界敏感、采集窗口不足、快扩散假设失效。
- 将 Fleury2009、Guo2016、Liebig1993、Noetinger2016、SCA2008 等未充分使用的 key 加入相关场景。
