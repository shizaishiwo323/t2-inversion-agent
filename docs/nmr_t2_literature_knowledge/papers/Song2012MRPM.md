---
citation_key: Song2012MRPM
pdf: "01_core_theory_inversion\Song2012_NMR_PorousMedia_t2t2.pdf"
category: 01_core_theory_inversion
tags: [core_theory_inversion, diffusive_coupling, eigenmodes, exchange, geometry, multidimensional_nmr, peak_merging, pore_coupling, pore_shape, pore_size, restricted_diffusion, short_t2, surface_relaxation, surface_relaxivity, t1_t2, t2_t2]
pages: 13
text_cache: "_extracted_text\Song2012_0d73b8398482bdeb.txt"
---

# Song2012MRPM

- **题名/文件**：Magnetic Resonance of Porous Media (MRPM): A perspective (`Song2012_NMR_PorousMedia_t2t2.pdf`)
- **建议引用格式**：`[@Song2012MRPM]`
- **原始来源**：`NMR Theory and Review\Song2012_NMR_PorousMedia_t2t2.pdf`
- **入选理由**：多孔介质 NMR、T2/T2 与孔隙耦合解释的理论综述背景。
- **在 T2 Agent 中的定位**：基础理论/反演背景引用；调用时只使用本卡片列出的具体机制，不要按大类泛化。

## Agent 可用结论

### 表面弛豫、孔径与短 T2
- **什么结果时调用**：当短 T2 面积高、主峰向短 T2 移动、小孔/高比表面积模型衰减更快，或需要解释 T2 与孔径关系时。
- **物理/数学机制**：有效横向弛豫通常由体相弛豫、表面弛豫和扩散相关项共同控制；在快扩散近似下，小孔或高表面积/体积比孔隙表现为更短 T2。
- **可写入报告的引用句式**：短 T2 组分通常支持更强表面弛豫、更小孔径或更高表面积/体积比的解释，但需要结合表面弛豫率和扩散区制判断。 [@Song2012MRPM]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 扩散耦合与孔间交换
- **什么结果时调用**：当多个预期孔群在反演中合并为宽峰、峰位落在几何预测之间、连通孔模型比孤立孔模型更平滑，或一维 T2 难以区分孔群时。
- **物理/数学机制**：自旋在不同孔隙尺度之间扩散交换，会把多个局部弛豫环境平均化；耦合强时，T2 分布不再直接等于各孔径群的独立响应。
- **可写入报告的引用句式**：峰合并或谱形变宽不一定说明只有一个孔群，也可能是孔间扩散耦合把多个弛豫环境混合后的结果。 [@Song2012MRPM]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### T2-T2/T1-T2 多维 NMR 与交换
- **什么结果时调用**：当一维 T2 谱无法区分耦合/交换、流体组分或复杂孔隙环境，需要说明二维 NMR 能提供更强约束时。
- **物理/数学机制**：二维相关实验把不同等待/混合期中的弛豫相关性编码进二维谱，可揭示交换、耦合和不同流体/孔隙环境之间的关联。
- **可写入报告的引用句式**：复杂样品的一维 T2 峰不总能唯一分配给物理孔群，多维 NMR 可作为验证和补充约束。 [@Song2012MRPM]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 受限扩散、几何与特征模态
- **什么结果时调用**：当几何改变导致 T2 峰位/峰宽改变，或圆孔、三角孔、复杂连通孔的结果不能用单一孔径解释时。
- **物理/数学机制**：有限孔域中的扩散-弛豫可看作边界条件控制的模态衰减问题；孔形、连通性和边界表面弛豫改变特征模态及有效弛豫时间。
- **可写入报告的引用句式**：T2 响应携带孔域扩散和边界弛豫共同作用后的有效模态信息，而不只是几何孔径本身。 [@Song2012MRPM]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

## 检索关键词

`core_theory_inversion`, `diffusive_coupling`, `eigenmodes`, `exchange`, `geometry`, `multidimensional_nmr`, `peak_merging`, `pore_coupling`, `pore_shape`, `pore_size`, `restricted_diffusion`, `short_t2`, `surface_relaxation`, `surface_relaxivity`, `t1_t2`, `t2_t2`

## 证据锚点（非原文长引）

- 摘要可抽取：是；结论/总结可抽取：是。
- 本卡片只保留机制级释义和检索标签；需要逐字引用或页码时，请打开对应 PDF 或 `_extracted_text` 缓存复核。
- 主要证据主题：表面弛豫、孔径与短 T2；扩散耦合与孔间交换；T2-T2/T1-T2 多维 NMR 与交换；受限扩散、几何与特征模态。

## 使用边界

- 不要把该文献当作所有样品的唯一解释依据；报告中应结合用户数据质量、T2 范围、正则化方式、模拟几何和参数设置。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。