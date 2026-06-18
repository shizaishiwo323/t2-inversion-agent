---
citation_key: Hagslatt2002RestrictiveGeometries
pdf: "03_numerical_methods_fem_lbm_matrix\Hagslatt2002_restrictiveGeometries.pdf"
category: 03_numerical_methods_fem_lbm_matrix
tags: [eigenmodes, geometry, numerical_methods_fem_lbm_matrix, pore_shape, pore_size, restricted_diffusion, short_t2, surface_relaxation, surface_relaxivity]
pages: 10
text_cache: "_extracted_text\Hagslatt2002_cf484411e73db7fb.txt"
---

# Hagslatt2002RestrictiveGeometries

- **题名/文件**：doi:10.1016/S1090-7807(02)00039-3 (`Hagslatt2002_restrictiveGeometries.pdf`)
- **建议引用格式**：`[@Hagslatt2002RestrictiveGeometries]`
- **原始来源**：`NMR simulation\FEM\Hagslatt2002_restrictiveGeometries.pdf`
- **入选理由**：限制几何中的扩散与弛豫模拟，适合解释理想孔隙模拟结果。
- **在 T2 Agent 中的定位**：数值方法引用；适合解释 FEM/FVM/LBM/矩阵方法、边界条件、内部梯度或特征模态。

## Agent 可用结论

### 受限扩散、几何与特征模态
- **什么结果时调用**：当几何改变导致 T2 峰位/峰宽改变，或圆孔、三角孔、复杂连通孔的结果不能用单一孔径解释时。
- **物理/数学机制**：有限孔域中的扩散-弛豫可看作边界条件控制的模态衰减问题；孔形、连通性和边界表面弛豫改变特征模态及有效弛豫时间。
- **可写入报告的引用句式**：T2 响应携带孔域扩散和边界弛豫共同作用后的有效模态信息，而不只是几何孔径本身。 [@Hagslatt2002RestrictiveGeometries]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

### 表面弛豫、孔径与短 T2
- **什么结果时调用**：当短 T2 面积高、主峰向短 T2 移动、小孔/高比表面积模型衰减更快，或需要解释 T2 与孔径关系时。
- **物理/数学机制**：有效横向弛豫通常由体相弛豫、表面弛豫和扩散相关项共同控制；在快扩散近似下，小孔或高表面积/体积比孔隙表现为更短 T2。
- **可写入报告的引用句式**：短 T2 组分通常支持更强表面弛豫、更小孔径或更高表面积/体积比的解释，但需要结合表面弛豫率和扩散区制判断。 [@Hagslatt2002RestrictiveGeometries]
- **证据定位**：见下方证据锚点；若没有页码锚点，则由题名、入选理由和文本关键词归类，正式引用前需复核原 PDF。

## 检索关键词

`eigenmodes`, `geometry`, `numerical_methods_fem_lbm_matrix`, `pore_shape`, `pore_size`, `restricted_diffusion`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## 证据锚点（非原文长引）

- 摘要可抽取：是；结论/总结可抽取：否。
- 本卡片只保留机制级释义和检索标签；需要逐字引用或页码时，请打开对应 PDF 或 `_extracted_text` 缓存复核。
- 主要证据主题：受限扩散、几何与特征模态；表面弛豫、孔径与短 T2。

## 使用边界

- 不要把该文献当作所有样品的唯一解释依据；报告中应结合用户数据质量、T2 范围、正则化方式、模拟几何和参数设置。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。