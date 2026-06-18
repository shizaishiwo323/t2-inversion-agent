---
citation_key: LucasOliveira2018RestrictedDiffusion
pdf: "02_pore_scale_simulation_random_walk\Lucas-Oliveira2018.pdf"
category: 02_pore_scale_simulation_random_walk
tags: [eigenmodes, forward_simulation, geometry, monte_carlo, pore_scale, pore_scale_simulation_random_walk, pore_shape, pore_size, random_walk, restricted_diffusion, short_t2, surface_relaxation, surface_relaxivity]
pages: 9
text_cache: "_extracted_text\Lucas2018_788c8a0586525cb4.txt"
---

# LucasOliveira2018RestrictedDiffusion

- **题名/文件**：Computational approach to integrate 3D X-ray microtomography and NMR data (`Lucas-Oliveira2018.pdf`)
- **建议引用格式**：`[@LucasOliveira2018RestrictedDiffusion]`
- **原始来源**：`NMR simulation\Random Walk\Lucas-Oliveira2018.pdf`
- **入选理由**：孔尺度随机游走/受限扩散模拟，对比反演谱和真实孔隙结构时有用。
- **在 T2 Agent 中的定位**：孔尺度随机游走/Monte Carlo 正演引用；适合解释模拟到衰减/T2 谱的机制链。
- **抽取备注**：PDF 可读，但有解析警告；若用于正式论文写作，请核对原文页码。

## Agent 可用结论

### 随机游走/Monte Carlo 正演模拟
- **什么结果时调用**：当需要解释随机游走为何能模拟 NMR 衰减、验证反演结果、或比较孔隙结构与反演 T2 谱时。
- **物理/数学机制**：随机游走把分子扩散离散为大量粒子轨迹，并在边界表面弛豫、体相弛豫和场不均匀条件下累积相位/衰减，生成可反演的 echo decay。
- **可写入报告的引用句式**：随机游走正演提供了从孔隙几何和物理参数到衰减曲线/T2 谱的机制桥梁。 [@LucasOliveira2018RestrictedDiffusion]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 受限扩散、几何与特征模态
- **什么结果时调用**：当几何改变导致 T2 峰位/峰宽改变，或圆孔、三角孔、复杂连通孔的结果不能用单一孔径解释时。
- **物理/数学机制**：有限孔域中的扩散-弛豫可看作边界条件控制的模态衰减问题；孔形、连通性和边界表面弛豫改变特征模态及有效弛豫时间。
- **可写入报告的引用句式**：T2 响应携带孔域扩散和边界弛豫共同作用后的有效模态信息，而不只是几何孔径本身。 [@LucasOliveira2018RestrictedDiffusion]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 表面弛豫、孔径与短 T2
- **什么结果时调用**：当短 T2 面积高、主峰向短 T2 移动、小孔/高比表面积模型衰减更快，或需要解释 T2 与孔径关系时。
- **物理/数学机制**：有效横向弛豫通常由体相弛豫、表面弛豫和扩散相关项共同控制；在快扩散近似下，小孔或高表面积/体积比孔隙表现为更短 T2。
- **可写入报告的引用句式**：短 T2 组分通常支持更强表面弛豫、更小孔径或更高表面积/体积比的解释，但需要结合表面弛豫率和扩散区制判断。 [@LucasOliveira2018RestrictedDiffusion]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

## 检索关键词

`eigenmodes`, `forward_simulation`, `geometry`, `monte_carlo`, `pore_scale`, `pore_scale_simulation_random_walk`, `pore_shape`, `pore_size`, `random_walk`, `restricted_diffusion`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## 证据锚点（非原文长引）

- 摘要可抽取：是；结论/总结可抽取：是。
- 本卡片只保留机制级释义和检索标签；需要逐字引用或页码时，请打开对应 PDF 或 `_extracted_text` 缓存复核。
- 主要证据主题：随机游走/Monte Carlo 正演模拟；受限扩散、几何与特征模态；表面弛豫、孔径与短 T2。

## 使用边界

- 不要把该文献当作所有样品的唯一解释依据；报告中应结合用户数据质量、T2 范围、正则化方式、模拟几何和参数设置。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。