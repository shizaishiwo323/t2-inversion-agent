---
citation_key: BrownsteinTarr1979
pdf: "01_core_theory_inversion\BrownsteinTarr1979.pdf"
category: 01_core_theory_inversion
tags: [core_theory_inversion, eigenmodes, geometry, pore_shape, pore_size, restricted_diffusion, short_t2, surface_relaxation, surface_relaxivity]
pages: 8
text_cache: "_extracted_text\BrownsteinTarr1979_966d259166178a66.txt"
---

# BrownsteinTarr1979

- **题名/文件**：Importance of classical diffusion in NMR studies of water in biological cells (`BrownsteinTarr1979.pdf`)
- **建议引用格式**：`[@BrownsteinTarr1979]`
- **原始来源**：`NMR Theory and Review\BrownsteinTarr1979.pdf`
- **入选理由**：孔隙表面弛豫、扩散受限与 T2-孔径解释的经典理论基础。
- **在 T2 Agent 中的定位**：基础理论引用：表面弛豫、受限扩散、几何/特征模态如何造成多指数衰减；不作为正则化或 L-curve 主引用。
- **抽取备注**：PDF 可读，但有解析警告；若用于正式论文写作，请核对原文页码。

## Agent 可用结论

### 表面弛豫、孔径与短 T2
- **什么结果时调用**：当短 T2 面积高、主峰向短 T2 移动、小孔/高比表面积模型衰减更快，或需要解释 T2 与孔径关系时。
- **物理/数学机制**：有效横向弛豫通常由体相弛豫、表面弛豫和扩散相关项共同控制；在快扩散近似下，小孔或高表面积/体积比孔隙表现为更短 T2。
- **可写入报告的引用句式**：短 T2 组分通常支持更强表面弛豫、更小孔径或更高表面积/体积比的解释，但需要结合表面弛豫率和扩散区制判断。 [@BrownsteinTarr1979]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 受限扩散、几何与特征模态
- **什么结果时调用**：当几何改变导致 T2 峰位/峰宽改变，或圆孔、三角孔、复杂连通孔的结果不能用单一孔径解释时。
- **物理/数学机制**：有限孔域中的扩散-弛豫可看作边界条件控制的模态衰减问题；孔形、连通性和边界表面弛豫改变特征模态及有效弛豫时间。
- **可写入报告的引用句式**：T2 响应携带孔域扩散和边界弛豫共同作用后的有效模态信息，而不只是几何孔径本身。 [@BrownsteinTarr1979]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

## 检索关键词

`core_theory_inversion`, `eigenmodes`, `geometry`, `pore_shape`, `pore_size`, `restricted_diffusion`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## 证据锚点（非原文长引）

- p.1 / cache line 8: 论文把多指数衰减归因于扩散方程和样品几何相关的特征值问题。
- p.1 / cache line 64: 文本给出包含体相 sink 与表面边界 sink 的扩散方程/边界条件框架。
- 主要证据主题：表面弛豫、孔径与短 T2；受限扩散、几何与特征模态。

## 使用边界

- 不要把该文献当作所有样品的唯一解释依据；报告中应结合用户数据质量、T2 范围、正则化方式、模拟几何和参数设置。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。