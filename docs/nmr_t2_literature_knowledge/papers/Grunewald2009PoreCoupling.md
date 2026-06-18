---
citation_key: Grunewald2009PoreCoupling
pdf: "04_pore_coupling_t2t2_interpretation\Grunewald2009_LabStudy_PoreCoupling.pdf"
category: 04_pore_coupling_t2t2_interpretation
tags: [component_assignment, diffusive_coupling, exchange, gaussian_decomposition, overfitting, peak_count, peak_merging, pore_coupling, pore_coupling_t2t2_interpretation, pore_size, short_t2, surface_relaxation, surface_relaxivity]
pages: 7
text_cache: "_extracted_text\Grunewald2009_75730560f5eceb3a.txt"
---

# Grunewald2009PoreCoupling

- **题名/文件**：A laboratory study of NMR relaxation times and pore coupling in heterogeneous media (`Grunewald2009_LabStudy_PoreCoupling.pdf`)
- **建议引用格式**：`[@Grunewald2009PoreCoupling]`
- **原始来源**：`NMR application\Lab NMR\Pore coupling\Grunewald2009_LabStudy_PoreCoupling.pdf`
- **入选理由**：实验与解释结合，但重点是 pore coupling，对模拟谱形解释有用。
- **在 T2 Agent 中的定位**：孔耦合/多维 NMR 解释引用；适合解释峰合并、交换和一维 T2 解释不唯一。

## Agent 可用结论

### 扩散耦合与孔间交换
- **什么结果时调用**：当多个预期孔群在反演中合并为宽峰、峰位落在几何预测之间、连通孔模型比孤立孔模型更平滑，或一维 T2 难以区分孔群时。
- **物理/数学机制**：自旋在不同孔隙尺度之间扩散交换，会把多个局部弛豫环境平均化；耦合强时，T2 分布不再直接等于各孔径群的独立响应。
- **可写入报告的引用句式**：峰合并或谱形变宽不一定说明只有一个孔群，也可能是孔间扩散耦合把多个弛豫环境混合后的结果。 [@Grunewald2009PoreCoupling]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 表面弛豫、孔径与短 T2
- **什么结果时调用**：当短 T2 面积高、主峰向短 T2 移动、小孔/高比表面积模型衰减更快，或需要解释 T2 与孔径关系时。
- **物理/数学机制**：有效横向弛豫通常由体相弛豫、表面弛豫和扩散相关项共同控制；在快扩散近似下，小孔或高表面积/体积比孔隙表现为更短 T2。
- **可写入报告的引用句式**：短 T2 组分通常支持更强表面弛豫、更小孔径或更高表面积/体积比的解释，但需要结合表面弛豫率和扩散区制判断。 [@Grunewald2009PoreCoupling]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 峰/组分解释边界（非 Gaussian 方法来源）
- **什么结果时调用**：当用户要求把 T2 谱分成 2-3 个峰并解释峰面积、峰位，或峰数改变导致解释变化时。
- **物理/数学机制**：Gaussian 分峰是在 log T2 轴上对谱形做经验近似；Whittall/Coates 等文献主要支撑“反演谱和组分解释需要谨慎”，不应被写成 Gaussian 方法来源。
- **可写入报告的引用句式**：分峰结果应作为解释辅助，而不是证明样品恰好存在相同数量物理孔群的唯一证据。 [@Grunewald2009PoreCoupling]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

## 检索关键词

`component_assignment`, `diffusive_coupling`, `exchange`, `gaussian_decomposition`, `overfitting`, `peak_count`, `peak_merging`, `pore_coupling`, `pore_coupling_t2t2_interpretation`, `pore_size`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## 证据锚点（非原文长引）

- 摘要可抽取：是；结论/总结可抽取：是。
- 本卡片只保留机制级释义和检索标签；需要逐字引用或页码时，请打开对应 PDF 或 `_extracted_text` 缓存复核。
- 主要证据主题：扩散耦合与孔间交换；表面弛豫、孔径与短 T2；峰/组分解释边界（非 Gaussian 方法来源）。

## 使用边界

- 不要把该文献当作所有样品的唯一解释依据；报告中应结合用户数据质量、T2 范围、正则化方式、模拟几何和参数设置。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。