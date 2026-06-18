---
citation_key: MatrixDiagonalization2002NMR
pdf: "03_numerical_methods_fem_lbm_matrix\1-s2.0-S0021979702984729-main.pdf"
category: 03_numerical_methods_fem_lbm_matrix
tags: [analytical_forward_model, eigenmodes, eigenvalues, geometry, matrix_diagonalization, numerical_methods_fem_lbm_matrix, pore_shape, restricted_diffusion]
pages: 12
text_cache: "_extracted_text\S1979_f7fe3cd43af32148.txt"
---

# MatrixDiagonalization2002NMR

- **题名/文件**：Magnetization Evolution in Network Models of Porous Rockunder Conditions of Drainage and Imbibition (`1-s2.0-S0021979702984729-main.pdf`)
- **建议引用格式**：`[@MatrixDiagonalization2002NMR]`
- **原始来源**：`NMR simulation\matrix diagonalization methods\1-s2.0-S0021979702984729-main.pdf`
- **入选理由**：矩阵对角化方法相关论文，补充特征值/模态解释。
- **在 T2 Agent 中的定位**：数值方法引用；适合解释 FEM/FVM/LBM/矩阵方法、边界条件、内部梯度或特征模态。

## Agent 可用结论

### 矩阵对角化/特征模态方法
- **什么结果时调用**：当需要解释为什么复杂衰减可以表示为多个特征模态叠加，或比较随机游走/FEM 与特征值正演方法时。
- **物理/数学机制**：扩散-弛豫算子离散后可用特征值/特征向量表示，衰减曲线由多个模态贡献组成；边界条件和孔隙状态改变特征谱。
- **可写入报告的引用句式**：多指数衰减可理解为扩散-弛豫系统多个特征模态叠加，而不仅是若干孤立孔群的简单相加。 [@MatrixDiagonalization2002NMR]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 受限扩散、几何与特征模态
- **什么结果时调用**：当几何改变导致 T2 峰位/峰宽改变，或圆孔、三角孔、复杂连通孔的结果不能用单一孔径解释时。
- **物理/数学机制**：有限孔域中的扩散-弛豫可看作边界条件控制的模态衰减问题；孔形、连通性和边界表面弛豫改变特征模态及有效弛豫时间。
- **可写入报告的引用句式**：T2 响应携带孔域扩散和边界弛豫共同作用后的有效模态信息，而不只是几何孔径本身。 [@MatrixDiagonalization2002NMR]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

## 检索关键词

`analytical_forward_model`, `eigenmodes`, `eigenvalues`, `geometry`, `matrix_diagonalization`, `numerical_methods_fem_lbm_matrix`, `pore_shape`, `restricted_diffusion`

## 证据锚点（非原文长引）

- 摘要可抽取：否；结论/总结可抽取：是。
- 本卡片只保留机制级释义和检索标签；需要逐字引用或页码时，请打开对应 PDF 或 `_extracted_text` 缓存复核。
- 主要证据主题：矩阵对角化/特征模态方法；受限扩散、几何与特征模态。

## 使用边界

- 不要把该文献当作所有样品的唯一解释依据；报告中应结合用户数据质量、T2 范围、正则化方式、模拟几何和参数设置。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。