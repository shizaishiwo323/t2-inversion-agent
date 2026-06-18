---
citation_key: Liebig1993RandomWalk
pdf: "02_pore_scale_simulation_random_walk\Leibig1993_RW.pdf"
category: 02_pore_scale_simulation_random_walk
tags: [eigenmodes, forward_simulation, geometry, monte_carlo, pore_scale, pore_scale_simulation_random_walk, pore_shape, random_walk, restricted_diffusion]
pages: 20
text_cache: "_extracted_text\Leibig1993_7fb4769e750827ba.txt"
---

# Liebig1993RandomWalk

- **题名/文件**：Leibig1993_RW (`Leibig1993_RW.pdf`)
- **建议引用格式**：`[@Liebig1993RandomWalk]`
- **原始来源**：`NMR simulation\Random Walk\Leibig1993_RW.pdf`
- **入选理由**：早期随机游走方法背景，可支持 Monte Carlo 模拟选择。
- **在 T2 Agent 中的定位**：孔尺度随机游走/Monte Carlo 正演引用；适合解释模拟到衰减/T2 谱的机制链。

## Agent 可用结论

### 随机游走/Monte Carlo 正演模拟
- **什么结果时调用**：当需要解释随机游走为何能模拟 NMR 衰减、验证反演结果、或比较孔隙结构与反演 T2 谱时。
- **物理/数学机制**：随机游走把分子扩散离散为大量粒子轨迹，并在边界表面弛豫、体相弛豫和场不均匀条件下累积相位/衰减，生成可反演的 echo decay。
- **可写入报告的引用句式**：随机游走正演提供了从孔隙几何和物理参数到衰减曲线/T2 谱的机制桥梁。 [@Liebig1993RandomWalk]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 受限扩散、几何与特征模态
- **什么结果时调用**：当几何改变导致 T2 峰位/峰宽改变，或圆孔、三角孔、复杂连通孔的结果不能用单一孔径解释时。
- **物理/数学机制**：有限孔域中的扩散-弛豫可看作边界条件控制的模态衰减问题；孔形、连通性和边界表面弛豫改变特征模态及有效弛豫时间。
- **可写入报告的引用句式**：T2 响应携带孔域扩散和边界弛豫共同作用后的有效模态信息，而不只是几何孔径本身。 [@Liebig1993RandomWalk]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

## 检索关键词

`eigenmodes`, `forward_simulation`, `geometry`, `monte_carlo`, `pore_scale`, `pore_scale_simulation_random_walk`, `pore_shape`, `random_walk`, `restricted_diffusion`

## 证据锚点（非原文长引）

- 摘要可抽取：是；结论/总结可抽取：否。
- 本卡片只保留机制级释义和检索标签；需要逐字引用或页码时，请打开对应 PDF 或 `_extracted_text` 缓存复核。
- 主要证据主题：随机游走/Monte Carlo 正演模拟；受限扩散、几何与特征模态。

## 使用边界

- 不要把该文献当作所有样品的唯一解释依据；报告中应结合用户数据质量、T2 范围、正则化方式、模拟几何和参数设置。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。