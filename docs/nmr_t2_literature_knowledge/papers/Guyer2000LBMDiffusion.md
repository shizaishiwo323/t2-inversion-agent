---
citation_key: Guyer2000LBMDiffusion
pdf: "03_numerical_methods_fem_lbm_matrix\Guyer2000_LBM.pdf"
category: 03_numerical_methods_fem_lbm_matrix
tags: [eigenmodes, geometry, lattice_boltzmann, lbm, numerical_methods_fem_lbm_matrix, pore_network, pore_shape, restricted_diffusion]
pages: 15
text_cache: "_extracted_text\Guyer2000_547b3892a8f1701c.txt"
---

# Guyer2000LBMDiffusion

- **题名/文件**：USING STANDARD SYSTE (`Guyer2000_LBM.pdf`)
- **建议引用格式**：`[@Guyer2000LBMDiffusion]`
- **原始来源**：`NMR simulation\LBM\Guyer2000_LBM.pdf`
- **入选理由**：Lattice Boltzmann 方法基础，作为 LBM 模拟解释支撑。
- **在 T2 Agent 中的定位**：数值方法引用；适合解释 FEM/FVM/LBM/矩阵方法、边界条件、内部梯度或特征模态。

## Agent 可用结论

### LBM 扩散/弛豫模拟
- **什么结果时调用**：当需要解释 lattice Boltzmann 方法为何适合孔尺度扩散、复杂边界和连通孔隙正演时。
- **物理/数学机制**：LBM 在格点上推进分布函数，能够处理复杂边界与孔隙连通结构中的扩散过程，并可与表面弛豫边界结合。
- **可写入报告的引用句式**：LBM 是连接数字孔隙结构和 NMR 衰减响应的一种孔尺度数值方法。 [@Guyer2000LBMDiffusion]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 受限扩散、几何与特征模态
- **什么结果时调用**：当几何改变导致 T2 峰位/峰宽改变，或圆孔、三角孔、复杂连通孔的结果不能用单一孔径解释时。
- **物理/数学机制**：有限孔域中的扩散-弛豫可看作边界条件控制的模态衰减问题；孔形、连通性和边界表面弛豫改变特征模态及有效弛豫时间。
- **可写入报告的引用句式**：T2 响应携带孔域扩散和边界弛豫共同作用后的有效模态信息，而不只是几何孔径本身。 [@Guyer2000LBMDiffusion]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

## 检索关键词

`eigenmodes`, `geometry`, `lattice_boltzmann`, `lbm`, `numerical_methods_fem_lbm_matrix`, `pore_network`, `pore_shape`, `restricted_diffusion`

## 证据锚点（非原文长引）

- 摘要可抽取：否；结论/总结可抽取：是。
- 本卡片只保留机制级释义和检索标签；需要逐字引用或页码时，请打开对应 PDF 或 `_extracted_text` 缓存复核。
- 主要证据主题：LBM 扩散/弛豫模拟；受限扩散、几何与特征模态。

## 使用边界

- 不要把该文献当作所有样品的唯一解释依据；报告中应结合用户数据质量、T2 范围、正则化方式、模拟几何和参数设置。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。