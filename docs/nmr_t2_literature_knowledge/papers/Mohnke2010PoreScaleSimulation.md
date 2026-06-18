---
citation_key: Mohnke2010PoreScaleSimulation
pdf: "03_numerical_methods_fem_lbm_matrix\Mohnke2010.pdf"
category: 03_numerical_methods_fem_lbm_matrix
tags: [dephasing, echo_spacing, eigenmodes, field_inhomogeneity, finite_element, finite_volume, geometry, internal_gradient, mesh, numerical_methods_fem_lbm_matrix, pde_solver, pore_shape, pore_size, restricted_diffusion, short_t2, surface_relaxation, surface_relaxivity]
pages: 12
text_cache: "_extracted_text\Mohnke2010_18e0c8f2e38f92aa.txt"
---

# Mohnke2010PoreScaleSimulation

- **题名/文件**：Microscale Simulations of NMR Relaxation in Porous Media Considering Internal Field Gradients (`Mohnke2010.pdf`)
- **建议引用格式**：`[@Mohnke2010PoreScaleSimulation]`
- **原始来源**：`NMR simulation\FEM\Mohnke2010.pdf`
- **入选理由**：孔尺度数值模拟、内部梯度/表面弛豫相关背景。
- **在 T2 Agent 中的定位**：孔尺度 FEM/内部梯度引用：表面弛豫、内部梯度和孔尺度有限元模拟。
- **抽取备注**：PDF 可读，但有解析警告；若用于正式论文写作，请核对原文页码。

## Agent 可用结论

### FEM/FVM 数值求解
- **什么结果时调用**：当模拟使用网格、有限元/有限体积、COMSOL 或内部梯度模型，需要解释边界条件、网格和数值解对衰减结果的影响时。
- **物理/数学机制**：FEM/FVM 通过求解扩散-弛豫偏微分方程计算孔域内磁化强度演化，边界条件编码表面弛豫，内部梯度或场项引入额外去相干。
- **可写入报告的引用句式**：网格型数值模拟可以把复杂孔隙几何、边界弛豫和内部梯度显式纳入 NMR 正演。 [@Mohnke2010PoreScaleSimulation]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 内部梯度/场不均匀
- **什么结果时调用**：当 simulated decay 比纯表面弛豫模型更快、长 T2 端被压低、echo spacing 改变影响谱形，或磁化率差异导致额外衰减时。
- **物理/数学机制**：内部磁场梯度与扩散耦合会造成附加去相干；这种项依赖扩散系数、梯度强度、echo spacing 和孔隙尺度。
- **可写入报告的引用句式**：T2 缩短不一定只来自小孔或高表面弛豫率，也可能来自内部梯度诱导的扩散去相干。 [@Mohnke2010PoreScaleSimulation]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 表面弛豫、孔径与短 T2
- **什么结果时调用**：当短 T2 面积高、主峰向短 T2 移动、小孔/高比表面积模型衰减更快，或需要解释 T2 与孔径关系时。
- **物理/数学机制**：有效横向弛豫通常由体相弛豫、表面弛豫和扩散相关项共同控制；在快扩散近似下，小孔或高表面积/体积比孔隙表现为更短 T2。
- **可写入报告的引用句式**：短 T2 组分通常支持更强表面弛豫、更小孔径或更高表面积/体积比的解释，但需要结合表面弛豫率和扩散区制判断。 [@Mohnke2010PoreScaleSimulation]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 受限扩散、几何与特征模态
- **什么结果时调用**：当几何改变导致 T2 峰位/峰宽改变，或圆孔、三角孔、复杂连通孔的结果不能用单一孔径解释时。
- **物理/数学机制**：有限孔域中的扩散-弛豫可看作边界条件控制的模态衰减问题；孔形、连通性和边界表面弛豫改变特征模态及有效弛豫时间。
- **可写入报告的引用句式**：T2 响应携带孔域扩散和边界弛豫共同作用后的有效模态信息，而不只是几何孔径本身。 [@Mohnke2010PoreScaleSimulation]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

## 检索关键词

`dephasing`, `echo_spacing`, `eigenmodes`, `field_inhomogeneity`, `finite_element`, `finite_volume`, `geometry`, `internal_gradient`, `mesh`, `numerical_methods_fem_lbm_matrix`, `pde_solver`, `pore_shape`, `pore_size`, `restricted_diffusion`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## 证据锚点（非原文长引）

- p.2 / cache line 6: 文本说明使用 FEM 在 pore scale 模拟 NMR processes。
- p.3 / cache line 161: 文本定义 surface relaxivity 并把其作为表面弛豫强度参数。
- p.3 / cache line 177: 文本说明 internal gradients 可由孔隙流体和基质磁化率差异造成，且不属于表面弛豫。
- 主要证据主题：FEM/FVM 数值求解；内部梯度/场不均匀；表面弛豫、孔径与短 T2；受限扩散、几何与特征模态。

## 使用边界

- 不要把该文献当作所有样品的唯一解释依据；报告中应结合用户数据质量、T2 范围、正则化方式、模拟几何和参数设置。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。