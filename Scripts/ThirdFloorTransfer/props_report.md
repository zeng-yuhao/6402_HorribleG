# Third-floor prop transfer report

Rooms 1–7 contain 773 original mesh instances. Every instance preserves source scale and material slots. Architecture is excluded and handled by the main level pass.

| Target | Source folder | Mesh instances | Main retained content |
|---|---|---:|---|
| 1 | ThirdFloor01Room01 | 100 | Office desk and upper section, side desk, sofa, leather chair, chair, 4 storage cabinet units and original books/documents. |
| 2 | ThirdFloor01Room04 | 99 | Autopsy table with sink and stains, 4 desks, 4 medical trolleys, instruments/medicines, 8 observer chairs and 2 hanging fixtures. |
| 3 | ThirdFloor01Room05 | 101 | Autopsy table with sink, one medical bed, desk, storage cabinet, 2 medical trolleys, one extra wall sink, tabletop instruments and wall posters. |
| 4 | ThirdFloor01Room07 | 170 | Administrative desk and upper section, 4 laboratory benches, 4 storage cabinets, leather chair and one small chair; flasks, racks, scales, books and paperwork. |
| 5 | ThirdFloor01Room02 | 184 | All 6 archive shelving units, 119 paper boxes, medication/flask stock and one chair. |
| 6 | ThirdFloor01Room06 | 83 | 4 sinks and mirrors, 3 toilets, 4 stall partitions, 66 connected pipe pieces, radiator and ceiling fixture. |
| 7 | ThirdFloor01Room05 | 36 | Second autopsy table with sink, desk, chair, 2 medical trolleys, radiator and original instruments. |

Layout changes preserve object size. Room 2 omits 20 balcony observer chairs and their associated surplus clutter because the requested surgery space has no balcony. Room 4 omits one duplicate cabinet and three auxiliary chairs to retain all five work surfaces and an accessible entry. Five spare radiator instances, one extra wall sink, two small chairs in Room 3 and two plumbing wall-return pieces were omitted where they conflicted with the target footprint. Original third-floor room 05 is split at source X=100 for targets 3 and 7, cropped to X −300..700 and Y below −2150.

The final navigation adjustment moves the Room 3 autopsy assembly 40 cm west and its southeast trolley 20 cm east as intact groups. The independent navigation pass uses a 70 cm diameter capsule proxy on a 10 cm grid; its final result is in navigation_qa_report.json.

props_delta_final.json applies the final changes to the first 775-instance import. It contains 11 transform updates and two lamp-bar deletions. decals_plan.json contains 12 floor stains, 3 autopsy/sink stains and 3 wall stains.
