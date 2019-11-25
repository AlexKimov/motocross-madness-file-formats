
### Formats
#### Motocross Madness (1998)

| № | Format/Ext | Progress   | Template (010 Editor) |  Description   |
| :-- | :------- | :-- | :-- | :-- | 
|  **1**  | DAT  |    | [DAT1.bt](https://github.com/AlexKimov/motocross-madness-file-formats/blob/master/templates/DAT1.bt) | Game resources file  |
|  **2**  | TRN  |    | [TRN.bt](https://github.com/AlexKimov/motocross-madness-file-formats/blob/master/templates/TRN.bt) | Track data  |
|  **3**  | VUB   |    | [VUB.bt](https://github.com/AlexKimov/motocross-madness-file-formats/blob/master/templates/VUB.bt) | Animations |

#### Motocross Madness 2 (2000)
| № | Format/Ext | Progress   | Template (010 Editor) |  Description   |
| :-- | :------- | :-- | :-- | :-- | 
|  **1**  |  DAT  |    | [DAT2.bt](https://github.com/AlexKimov/motocross-madness-file-formats/blob/master/templates/DAT2.bt) | Game resources file  |
|  **2**  |  ESB  |    | [DAT2.bt](./blob/master/templates/ESB.bt) | Track eco system definitions binary  |
|  **3**  |  TDF  |    | [DAT2.bt](./blob/master/templates/TDF.bt) | Track definition (border splines)  |
|  **4**  |  SLB  |    | [DAT2.bt](./blob/master/templates/SLB.bt) | Game models binary  |
|  **5**  |  TGA  |    | [DAT2.bt](./blob/master/templates/TGA2.bt) | Game LZW compressed bitmaps  |
### Scripts
* [DecodeRES.1sc](https://github.com/AlexKimov/motocross-madness-file-formats/blob/master/scripts/DecodeRES.1sc) - script to decode MM2 .dat files
* [unpackDAT.1sc](https://github.com/AlexKimov/motocross-madness-file-formats/blob/master/scripts/unpackDAT.1sc) - script to unpack MM1 .dat files
* [unpackDAT2.1sc](https://github.com/AlexKimov/motocross-madness-file-formats/blob/master/scripts/unpackDAT2.1sc) - script to unpack MM2 .dat files
