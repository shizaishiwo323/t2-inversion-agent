---
citation_key: Tandon2018FiniteVolumeInternalGradients
pdf: "03_numerical_methods_fem_lbm_matrix\Tandon2018_FiniteVolumeMethod_InternalGradients.pdf"
category: 03_numerical_methods_fem_lbm_matrix
tags: [dephasing, echo_spacing, eigenmodes, field_inhomogeneity, finite_element, finite_volume, geometry, internal_gradient, mesh, numerical_methods_fem_lbm_matrix, pde_solver, pore_shape, restricted_diffusion]
pages: 18
text_cache: "_extracted_text\Tandon2018_4c00fcb57fd69350.txt"
---

# Tandon2018FiniteVolumeInternalGradients

- **题名/文件**：Effect of Internal Magnetic-Field Gradients on Nuclear-Magnetic-Resonance Measurements and Nuclear-Magnetic-Resonance-Based (`Tandon2018_FiniteVolumeMethod_InternalGradients.pdf`)
- **建议引用格式**：`[@Tandon2018FiniteVolumeInternalGradients]`
- **原始来源**：`NMR simulation\FEM\Tandon2018_FiniteVolumeMethod_InternalGradients.pdf`
- **入选理由**：有限体积法和内部梯度效应，适合解释数值模型边界条件/梯度影响。
- **在 T2 Agent 中的定位**：数值方法引用；适合解释 FEM/FVM/LBM/矩阵方法、边界条件、内部梯度或特征模态。

## Agent 可用结论

### FEM/FVM 数值求解
- **什么结果时调用**：当模拟使用网格、有限元/有限体积、COMSOL 或内部梯度模型，需要解释边界条件、网格和数值解对衰减结果的影响时。
- **物理/数学机制**：FEM/FVM 通过求解扩散-弛豫偏微分方程计算孔域内磁化强度演化，边界条件编码表面弛豫，内部梯度或场项引入额外去相干。
- **可写入报告的引用句式**：网格型数值模拟可以把复杂孔隙几何、边界弛豫和内部梯度显式纳入 NMR 正演。 [@Tandon2018FiniteVolumeInternalGradients]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 内部梯度/场不均匀
- **什么结果时调用**：当 simulated decay 比纯表面弛豫模型更快、长 T2 端被压低、echo spacing 改变影响谱形，或磁化率差异导致额外衰减时。
- **物理/数学机制**：内部磁场梯度与扩散耦合会造成附加去相干；这种项依赖扩散系数、梯度强度、echo spacing 和孔隙尺度。
- **可写入报告的引用句式**：T2 缩短不一定只来自小孔或高表面弛豫率，也可能来自内部梯度诱导的扩散去相干。 [@Tandon2018FiniteVolumeInternalGradients]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 受限扩散、几何与特征模态
- **什么结果时调用**：当几何改变导致 T2 峰位/峰宽改变，或圆孔、三角孔、复杂连通孔的结果不能用单一孔径解释时。
- **物理/数学机制**：有限孔域中的扩散-弛豫可看作边界条件控制的模态衰减问题；孔形、连通性和边界表面弛豫改变特征模态及有效弛豫时间。
- **可写入报告的引用句式**：T2 响应携带孔域扩散和边界弛豫共同作用后的有效模态信息，而不只是几何孔径本身。 [@Tandon2018FiniteVolumeInternalGradients]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

## 检索关键词

`dephasing`, `echo_spacing`, `eigenmodes`, `field_inhomogeneity`, `finite_element`, `finite_volume`, `geometry`, `internal_gradient`, `mesh`, `numerical_methods_fem_lbm_matrix`, `pde_solver`, `pore_shape`, `restricted_diffusion`

## 证据锚点（非原文长引）

- 摘要可抽取：否；结论/总结可抽取：是。
- 本卡片只保留机制级释义和检索标签；需要逐字引用或页码时，请打开对应 PDF 或 `_extracted_text` 缓存复核。
- 主要证据主题：FEM/FVM 数值求解；内部梯度/场不均匀；受限扩散、几何与特征模态。

## 使用边界

- 不要把该文献当作所有样品的唯一解释依据；报告中应结合用户数据质量、T2 范围、正则化方式、模拟几何和参数设置。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。