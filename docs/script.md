# Presentation Script — Automated Shoreline Analysis
**Mapathon 2025 | Anup Bagde | Registration ID: MPS051**
**Duration: ~10 minutes | 9 Slides**

---

> 💡 **How to use this script:**
> - Read it 2–3 times before presenting
> - Keep it open on a second screen or as a printed copy beside you
> - You don't need to say every word exactly — use it as a guide
> - **[CUE]** means click to next slide or next animation
> - *[italic text]* = stage direction for you, don't say it out loud

---

---

## SLIDE 1 — Title Slide
*[Wait 2–3 seconds after joining the call, smile, then begin]*

"Good morning everyone. Thank you for this opportunity.

My name is Anup Bagde. I work as a Project Engineer at Centre for Development of Advanced Computing — CDAC Pune.

My background is primarily in software development. I recently got into GIS and geospatial work because at CDAC our group HPC-ESEG, we work on flood simulation and tsunami simulation on High Performance Computing systems. So coastal and water-related problems are very much part of our day-to-day work.

This submission was done together with my mentor and manager, Girishchandra Yendargaye, who is a Scientist D at CDAC. He guided me through the geospatial aspects of this solution. Without his guidance this would not have been possible.

We participated in this Mapathon because the problem — automated shoreline extraction — connects directly to what we do. SHORELINE_DATA is important for our flood and tsunami models. So this was both a learning opportunity and practically relevant to our work.

Our Registration ID is MPS051.

Today I will take you through our approach, the pipeline we built, the results, and where we see this going."

I also want to mention — we came across this Mapathon a bit late, and given our ongoing project workload at CDAC, we had limited time to work on this. What we are presenting today is an honest proof of concept — it works, it is validated, but it is not a complete solution. We are aware of the gaps and I will talk about them openly.

**[CUE → Click to Slide 2]**

---

---

## SLIDE 2 — Problem Understanding
*[Look at left column]*

"Let me first quickly show that we understood what was asked.

The problem statement had some clear requirements — extract shorelines automatically from satellite images taken at different times, account for tidal variation, detect how the shoreline is changing over time, and validate the results using beach profile data.

**[CUE → Click to reveal right column]**

On the right side you can see what we addressed.

We built a fully automated extraction pipeline. We ran analysis across three time periods. And we validated at four GPS beach reference locations.

I want to be honest here — tidal correction is not implemented in this version. What we extracted are instantaneous shorelines — the position at the time of the satellite pass. Proper tidal normalisation is our top priority for the next version. I will come back to this in the limitations slide."

**[CUE → Click to Slide 3]**

---

---

## SLIDE 3 — Data Used
*[Point to Box 1]*

"The satellite imagery was provided by the Mapathon organizers — Landsat 8, Level-2 Surface Reflectance product. The study area covers four beaches along the Tamil Nadu coast — Sayalkudi, T.Mariyur, Keelvaipar, and Ervadi — spanning roughly 100 kilometres of coastline.

Level-2 product means the images are already corrected for atmospheric effects — so the reflectance values represent actual ground surface properties, not atmospheric noise. This is important for reliable water index calculation.

From these images, we use two bands — Band 3, which is Green, and Band 5, which is Near Infrared. I will explain why these two specifically in the next slide

**[CUE → Click to reveal Box 2]**

The problem asked for monthly data for 2023, excluding September, October, and November — that is nine months. The organizers provided images for all those months. However due to our time constraint, we worked with only three scenes that were clearly usable — April 18th, May 20th, and August 24th, 2023 — where cloud cover over the study area was minimal.

The remaining months do have cloud cover issues, but with more time we could have handled this — Landsat provides a Quality Assessment band which can be used to mask cloudy pixels, and gap-filling techniques exist to reconstruct usable data. That is something we plan to do in the next version.

**[CUE → Click to reveal Box 3]**

For reference data — we used the AOI polygon to clip our analysis to the study region, four GPS beach reference points for validation."

**[CUE → Click to Slide 4]**

---

---

## SLIDE 4 — Methodology / Pipeline
*[This is your most important slide. Take your time. Click step by step.]*

"Now let me walk you through the automated pipeline.

The entire pipeline is written in Python. Three scripts — one for extraction, one for change detection, and one for summary statistics. I will explain each step as I go.

**[CUE → Click — Input box appears]**

The input is two raster files from Landsat — Band 3, Green, and Band 5, Near Infrared — for each date.

**[CUE → Click — Step 1: NDWI appears]**

Step one is calculating the NDWI — Normalized Difference Water Index.

The formula is: Green minus NIR, divided by Green plus NIR.

Why these two bands? Water absorbs Near Infrared strongly and reflects Green light. Land and vegetation do the opposite — they reflect NIR and absorb visible light. So when you take this ratio, water pixels give a positive value, land pixels give a negative value, and the boundary between water and land — the shoreline — sits at zero.

In the code, we add a very small number — 1e-10 — to the denominator to avoid division by zero in dry areas.

**[CUE → Click — Step 2: AOI Clipping appears]**

Step two — we clip the NDWI raster to the Area of Interest polygon. This removes the ocean far offshore and inland areas, so we focus only on the coastal zone. We use rasterio's mask function for this.

**[CUE → Click — Step 3: NoData Filling appears]**

Step three — NoData filling. Satellite images sometimes have missing pixels — due to scan line errors or edge effects. These gaps can break the shoreline contour. So we fill them using nearest neighbour interpolation within a 5 pixel search radius using rasterio's fillnodata function.

**[CUE → Click — Step 4: Contour Extraction appears]**

Step four — contour extraction. We call GDAL's gdal_contour tool via subprocess. We ask it to extract the contour at NDWI equals zero. This gives us a line — or multiple lines — representing everywhere the NDWI transitions from positive to negative. That zero crossing is the water-land boundary.

**[CUE → Click — Step 5: Proximity Filtering appears]**

Step five — filtering. NDWI zero contours can include many things — small ponds, rivers, irrigation canals. We do not want those. So we filter in two ways. First, we keep only contours longer than 10 kilometres — this removes small water bodies. Second, among the remaining contours, we pick the one that is closest to our GPS beach reference points. This ensures we are selecting the actual coastline and not some inland water feature.

**[CUE → Click — Output appears]**

The output is a shoreline vector saved as a GeoPackage file, with attributes — date, length, source scene ID, and extraction method.

The complete pipeline — extraction, change detection, and summary — runs in under 25 seconds on a standard laptop. CPU-only, no GPU needed."

**[CUE → Click to Slide 5]**

---

---

## SLIDE 5 — Results
*[Point to table first, then change stats, then map]*

"Here are the results.

**[CUE → Click — length table appears]**

We extracted shorelines for all three months. The lengths are 99,720 metres for April, 96,501 for May, and 97,358 for August — all roughly 97 to 100 kilometres. The consistency across months is actually a good sign — it means the pipeline is stable and not producing wildly different results due to noise.

**[CUE → Click — change stats appear]**

For shoreline change — we measured positional shifts at each beach reference point using a perpendicular transect method. At each beach point, we draw a line perpendicular to the shoreline and measure where each month's shoreline intersects that line. The distance between those intersections is the shoreline change.

The maximum change detected was 10.69 metres at Keelvaipar Beach between April and May.

Now — at 30 metre pixel resolution, detecting a 10 metre change might seem optimistic. But NDWI contours are sub-pixel accurate because we are extracting a mathematical zero crossing, not a pixel boundary. So metre-scale detection is reasonable here.

**[CUE → Click — map appears]**

This is our multi-temporal shoreline map. Blue is August, green is May, red is April. The four beach reference points are marked. You can see the three shorelines running along the coast — they are very close together, which is consistent with the small change values we measured."

**[CUE → Click to Slide 6]**

---

---

## SLIDE 6 — Validation
*[Keep calm and confident here — this slide is straightforward]*

"To validate our automated results, we also manually extracted shorelines in QGIS using the same NDWI rasters.

**[CUE → Click — left column]**

The approach was simple — load the same NDWI file in QGIS, visually identify the zero boundary, and digitize the shoreline manually. We did this for all three months. This gives us a human-verified reference to compare against.

**[CUE → Click — right column]**

The comparison showed that the automated pipeline results were consistent with the manual extraction. The positional difference was within one to two pixels — 30 to 60 metres — which is acceptable at 30 metre Landsat resolution.

Both methods also showed the same seasonal pattern of change, which confirms the pipeline is capturing real coastal dynamics and not artifacts.

I want to be careful not to overstate accuracy here — at 30 metre resolution, we cannot detect very small changes. But for regional-scale coastal monitoring, the pipeline performs reliably."

**[CUE → Click to Slide 7]**

---

---

## SLIDE 7 — Limitations & Honest Gaps
*[Speak calmly here — being honest is a strength, not a weakness]*

"I want to be upfront about the limitations of this work. We think it is important to know what your system cannot do, not just what it can.

**[CUE → Click — bullets appear one by one as you speak each one]**

First — tidal normalisation is not implemented. We have the HTL and LTL data, and we understand the concept — that shoreline position shifts with tide level, so to compare shorelines across dates fairly, you need to correct them to the same tidal datum. We did not implement this correction in this version. It is the most important gap.

Second — we only had three usable months out of nine due to cloud cover. This limits the temporal resolution of our analysis.

Third — Landsat has 30 metre pixel resolution. This means any shoreline shift smaller than roughly 15 metres is difficult to detect reliably. Higher resolution data like Sentinel-2 at 10 metres, or commercial data, would improve this.

Fourth — beach profile validation is limited. We used a single-date profile for reference. A full 3D validation with multi-date profiles was not done.

Fifth — we do not currently flag anomalous shoreline positions — for example, positions affected by storm surges or extreme tidal events. A production system would need this.

These are known gaps and they form the basis of our roadmap."

**[CUE → Click to Slide 8]**

---

---

## SLIDE 8 — Future Roadmap
*[This slide shows vision — speak with a bit more energy here]*

"Based on what we have built, here is where we see this going.

**[CUE → Click — Near Term box appears]**

In the near term — the first priority is implementing full tidal correction using the HTL and LTL data. Second, expanding temporal coverage by using Sentinel-2 data, which gives 10 metre resolution and 5-day revisit. Third, adding automated cloud masking so we do not have to manually check cloud cover.

**[CUE → Click — Medium Term box appears]**

In the medium term — we want to apply machine learning to improve shoreline boundary detection, especially in areas where NDWI alone struggles — shallow water, turbid water, and mixed sand-rock boundaries. We also want full 3D validation using the beach profile data.

**[CUE → Click — Long Term box appears]**

Long term — deploying this on HPC infrastructure for national scale monitoring, building a real-time erosion alert system, and integrating with coastal management dashboards.

**[CUE → Click — Integration section appears]**

But more importantly — this is not just future work on paper. At CDAC, we have two existing systems where this directly fits.

The first is our C-Flood portal — this is CDAC's operational flood simulation platform for the Mahanadi Delta. Tidal input is already part of that simulation. Integrating dynamic SHORELINE_DATA from this pipeline as a module would improve the coastal boundary conditions of the flood model.

The second is the EU Ganana project — under the Natural Hazards work package, we are working on tsunami simulation. Accurate and up-to-date SHORELINE_DATA is critical for defining the coastal boundary in tsunami propagation models. This pipeline can directly feed into that."

**[CUE → Click to Slide 9]**

---

---

## SLIDE 9 — Conclusion
*[Speak slowly and clearly — this is your closing, make it land]*

"To summarize —

**[CUE → Click — bullets appear one by one]**

We built a fully automated, reproducible shoreline extraction pipeline in Python using open-source tools — rasterio, GDAL, GeoPandas, and Shapely.

We validated it across three time periods and at four GPS reference locations.

We detected shoreline changes at the metre scale — maximum 10.69 metres at Keelvaipar Beach.

The automated results are consistent with manual QGIS extraction.

Processing time is about 25 sec for whole pipeline, which scales well.

And the entire stack is open-source — freely deployable without any licensing cost.

**[CUE → Click — map appears]**

This is a working, validated proof of concept. It is not complete — we have acknowledged the gaps honestly. But it demonstrates that the core approach is sound and the pipeline is functional.

Given that our team already works on flood and tsunami simulation at CDAC, this is not a standalone experiment. There is a real home for this work in systems we are actively building.

Thank you for your time. I am happy to take questions."

*[Breathe. Smile. Wait.]*

---

---

## Q&A — Likely Questions & How to Answer

*[Keep answers short. It is okay to say "that is a good point, we have not done that yet."]*

---

**Q: Why did you use NDWI and not other indices like MNDWI or AWEI?**

"NDWI using Green and NIR is the most established method for shoreline detection — McFeeters 1996. For this coastal region with clear water and sandy beaches, it works well. MNDWI uses SWIR instead of NIR and can handle turbid water better. That is a valid improvement we can explore in the next version."

---

**Q: How did you handle tidal correction?**

"Honestly, tidal correction is not implemented in this version. The HTL and LTL data was provided but we did not get to incorporating it due to time constraints. What we have extracted are instantaneous shorelines — the position at the time of the satellite pass — not tide-normalised shorelines. Full tidal correction is our top priority for the next version"

---

**Q: Why only 3 months? The problem asked for 9.**

"The remaining months had significant cloud cover over the study area. Optical satellite data cannot penetrate clouds. We selected only cloud-free scenes to ensure data quality. In future we plan to use SAR data — Synthetic Aperture Radar — which works through clouds."

---

**Q: How accurate is your shoreline at 30m resolution?**

"The contour is extracted at the NDWI zero crossing, which is a sub-pixel mathematical boundary. So the accuracy is better than one pixel. However the practical limit for detecting change is roughly half a pixel — around 15 metres. For regional monitoring at 100km scale, this is acceptable."

---

**Q: Did you apply any machine learning?**

"Not in this version — the pipeline is fully rule-based. NDWI thresholding at zero, length filtering, and proximity selection. ML-based refinement is in our medium term roadmap, especially for improving detection in turbid or shallow water areas."

---

**Q: How does this connect to your work at CDAC?**

"At CDAC we run flood simulation on the Mahanadi Delta through our C-Flood portal, and tsunami simulation under the EU Gyana project. Both models need accurate coastal boundary conditions. Shoreline position is a direct input. So this pipeline can be integrated as a module into both systems."

---

**Q: What would you do differently if you had more time?**

"Three things — implement full tidal normalisation, use Sentinel-2 for higher resolution and more monthly coverage, and add ML-based post processing to handle edge cases where NDWI alone is not sufficient."

---

*End of Script*