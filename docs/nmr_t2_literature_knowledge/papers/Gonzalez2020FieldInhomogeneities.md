---
citation_key: Gonzalez2020FieldInhomogeneities
pdf: "02_pore_scale_simulation_random_walk\Gonzalez2020_Inhomogeneities .pdf"
category: 02_pore_scale_simulation_random_walk
tags: [dephasing, echo_spacing, eigenmodes, field_inhomogeneity, forward_simulation, geometry, internal_gradient, monte_carlo, pore_scale, pore_scale_simulation_random_walk, pore_shape, random_walk, restricted_diffusion]
pages: 15
text_cache: "_extracted_text\Gonzalez2020_18d700806668cecf.txt"
---

# Gonzalez2020FieldInhomogeneities

- **题名/文件**：Simulations of NMR Relaxation in a Real Porous Structure: Pre-asymptotic Behavior to the Localization Regime (`Gonzalez2020_Inhomogeneities .pdf`)
- **建议引用格式**：`[@Gonzalez2020FieldInhomogeneities]`
- **原始来源**：`NMR simulation\Random Walk\Gonzalez2020_Inhomogeneities .pdf`
- **入选理由**：非均匀场/内部梯度对 NMR 响应的影响，可解释模拟与反演之间的偏差来源。
- **在 T2 Agent 中的定位**：孔尺度随机游走/Monte Carlo 正演引用；适合解释模拟到衰减/T2 谱的机制链。

## Agent 可用结论

### 内部梯度/场不均匀
- **什么结果时调用**：当 simulated decay 比纯表面弛豫模型更快、长 T2 端被压低、echo spacing 改变影响谱形，或磁化率差异导致额外衰减时。
- **物理/数学机制**：内部磁场梯度与扩散耦合会造成附加去相干；这种项依赖扩散系数、梯度强度、echo spacing 和孔隙尺度。
- **可写入报告的引用句式**：T2 缩短不一定只来自小孔或高表面弛豫率，也可能来自内部梯度诱导的扩散去相干。 [@Gonzalez2020FieldInhomogeneities]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 随机游走/Monte Carlo 正演模拟
- **什么结果时调用**：当需要解释随机游走为何能模拟 NMR 衰减、验证反演结果、或比较孔隙结构与反演 T2 谱时。
- **物理/数学机制**：随机游走把分子扩散离散为大量粒子轨迹，并在边界表面弛豫、体相弛豫和场不均匀条件下累积相位/衰减，生成可反演的 echo decay。
- **可写入报告的引用句式**：随机游走正演提供了从孔隙几何和物理参数到衰减曲线/T2 谱的机制桥梁。 [@Gonzalez2020FieldInhomogeneities]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 受限扩散、几何与特征模态
- **什么结果时调用**：当几何改变导致 T2 峰位/峰宽改变，或圆孔、三角孔、复杂连通孔的结果不能用单一孔径解释时。
- **物理/数学机制**：有限孔域中的扩散-弛豫可看作边界条件控制的模态衰减问题；孔形、连通性和边界表面弛豫改变特征模态及有效弛豫时间。
- **可写入报告的引用句式**：T2 响应携带孔域扩散和边界弛豫共同作用后的有效模态信息，而不只是几何孔径本身。 [@Gonzalez2020FieldInhomogeneities]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

## 检索关键词

`dephasing`, `echo_spacing`, `eigenmodes`, `field_inhomogeneity`, `forward_simulation`, `geometry`, `internal_gradient`, `monte_carlo`, `pore_scale`, `pore_scale_simulation_random_walk`, `pore_shape`, `random_walk`, `restricted_diffusion`

## 证据锚点（非原文长引）

- 摘要可抽取：是；结论/总结可抽取：是。
- 本卡片只保留机制级释义和检索标签；需要逐字引用或页码时，请打开对应 PDF 或 `_extracted_text` 缓存复核。
- 主要证据主题：内部梯度/场不均匀；随机游走/Monte Carlo 正演模拟；受限扩散、几何与特征模态。

## 使用边界

- 不要把该文献当作所有样品的唯一解释依据；报告中应结合用户数据质量、T2 范围、正则化方式、模拟几何和参数设置。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。