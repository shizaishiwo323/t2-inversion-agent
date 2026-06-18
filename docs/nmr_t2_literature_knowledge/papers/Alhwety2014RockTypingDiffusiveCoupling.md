---
citation_key: Alhwety2014RockTypingDiffusiveCoupling
pdf: "02_pore_scale_simulation_random_walk\Alhwety2014_Rock-typing_DiffCoupl.pdf"
category: 02_pore_scale_simulation_random_walk
tags: [dephasing, diffusive_coupling, echo_spacing, exchange, field_inhomogeneity, forward_simulation, internal_gradient, monte_carlo, peak_merging, pore_coupling, pore_scale, pore_scale_simulation_random_walk, pore_size, random_walk, short_t2, surface_relaxation, surface_relaxivity]
pages: 7
text_cache: "_extracted_text\Alhwety2014_0ef32964002fc030.txt"
---

# Alhwety2014RockTypingDiffusiveCoupling

- **题名/文件**：DF_Alhwety_v4_final_nodate (`Alhwety2014_Rock-typing_DiffCoupl.pdf`)
- **建议引用格式**：`[@Alhwety2014RockTypingDiffusiveCoupling]`
- **原始来源**：`NMR simulation\Random Walk\Alhwety2014_Rock-typing_DiffCoupl.pdf`
- **入选理由**：扩散耦合、T2 分布与岩石类型解释之间的模拟/解释连接。
- **在 T2 Agent 中的定位**：孔尺度随机游走/Monte Carlo 正演引用；适合解释模拟到衰减/T2 谱的机制链。

## Agent 可用结论

### 扩散耦合与孔间交换
- **什么结果时调用**：当多个预期孔群在反演中合并为宽峰、峰位落在几何预测之间、连通孔模型比孤立孔模型更平滑，或一维 T2 难以区分孔群时。
- **物理/数学机制**：自旋在不同孔隙尺度之间扩散交换，会把多个局部弛豫环境平均化；耦合强时，T2 分布不再直接等于各孔径群的独立响应。
- **可写入报告的引用句式**：峰合并或谱形变宽不一定说明只有一个孔群，也可能是孔间扩散耦合把多个弛豫环境混合后的结果。 [@Alhwety2014RockTypingDiffusiveCoupling]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 随机游走/Monte Carlo 正演模拟
- **什么结果时调用**：当需要解释随机游走为何能模拟 NMR 衰减、验证反演结果、或比较孔隙结构与反演 T2 谱时。
- **物理/数学机制**：随机游走把分子扩散离散为大量粒子轨迹，并在边界表面弛豫、体相弛豫和场不均匀条件下累积相位/衰减，生成可反演的 echo decay。
- **可写入报告的引用句式**：随机游走正演提供了从孔隙几何和物理参数到衰减曲线/T2 谱的机制桥梁。 [@Alhwety2014RockTypingDiffusiveCoupling]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 表面弛豫、孔径与短 T2
- **什么结果时调用**：当短 T2 面积高、主峰向短 T2 移动、小孔/高比表面积模型衰减更快，或需要解释 T2 与孔径关系时。
- **物理/数学机制**：有效横向弛豫通常由体相弛豫、表面弛豫和扩散相关项共同控制；在快扩散近似下，小孔或高表面积/体积比孔隙表现为更短 T2。
- **可写入报告的引用句式**：短 T2 组分通常支持更强表面弛豫、更小孔径或更高表面积/体积比的解释，但需要结合表面弛豫率和扩散区制判断。 [@Alhwety2014RockTypingDiffusiveCoupling]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 内部梯度/场不均匀
- **什么结果时调用**：当 simulated decay 比纯表面弛豫模型更快、长 T2 端被压低、echo spacing 改变影响谱形，或磁化率差异导致额外衰减时。
- **物理/数学机制**：内部磁场梯度与扩散耦合会造成附加去相干；这种项依赖扩散系数、梯度强度、echo spacing 和孔隙尺度。
- **可写入报告的引用句式**：T2 缩短不一定只来自小孔或高表面弛豫率，也可能来自内部梯度诱导的扩散去相干。 [@Alhwety2014RockTypingDiffusiveCoupling]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

## 检索关键词

`dephasing`, `diffusive_coupling`, `echo_spacing`, `exchange`, `field_inhomogeneity`, `forward_simulation`, `internal_gradient`, `monte_carlo`, `peak_merging`, `pore_coupling`, `pore_scale`, `pore_scale_simulation_random_walk`, `pore_size`, `random_walk`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## 证据锚点（非原文长引）

- 摘要可抽取：是；结论/总结可抽取：是。
- 本卡片只保留机制级释义和检索标签；需要逐字引用或页码时，请打开对应 PDF 或 `_extracted_text` 缓存复核。
- 主要证据主题：扩散耦合与孔间交换；随机游走/Monte Carlo 正演模拟；表面弛豫、孔径与短 T2；内部梯度/场不均匀。

## 使用边界

- 不要把该文献当作所有样品的唯一解释依据；报告中应结合用户数据质量、T2 范围、正则化方式、模拟几何和参数设置。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。