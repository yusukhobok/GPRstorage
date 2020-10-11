import numpy as np
import struct
import os
import pandas as pd
import pickle

CURRENT_FILE_FORMAT_VERSION = 49

def change_color(col):
    if col == "blue": return "b"
    elif col == "green": return "g"
    elif col == "red": return "r"
    elif col == "cyan": return "c"
    elif col == "magenta": return "m"
    elif col == "yellow": return "y"
    elif col == "black": return "k"
    elif col == "white": return "w"
    else: return col


def read_string(f, length: int = 256):
    value, = struct.unpack(f"{length}s", f.read(struct.calcsize(f"{length}s")))
    value = value.decode("utf-8", "ignore")
    value = value.replace("\x00", "")
    return value


def load_rdr(FileName, OldVersion = False):
    try:
        print("load_rdr", FileName)
        with open(FileName, "rb") as f:
            def decompressFromFile():
                try:
                    count, = struct.unpack("i", f.read(struct.calcsize("i")))
                    compr = f.read(count)
                    import zlib
                    return zlib.decompress(compr)
                except MemoryError:
                    return None

            #Загрузка версии формата файла
            Version = None
            if not OldVersion:
                Version, =  struct.unpack("i", f.read(struct.calcsize("i")))

            if Version > CURRENT_FILE_FORMAT_VERSION:
                print("Файл создан в более новой версии программы. Открытие невозможно")
                return None

            if Version < 37:
                Notes = ""
            else:
                Notes = read_string(f)

            HistoryCaptions = []
            if Version >= 38:
                HistoryCaptionsCount, = struct.unpack("i", f.read(struct.calcsize("i")))
                for i in range(HistoryCaptionsCount):
                    caption = read_string(f)
                    HistoryCaptions.append(caption)

            #Загрузка ссылок на следующую и предыдующую радарограммы
            if Version >= 31:
                IsPrevRadFileName, = struct.unpack("?", f.read(struct.calcsize("?")))
                if IsPrevRadFileName:
                    PrevRadFileName = read_string(f)
                else:
                    PrevRadFileName = None
                IsNextRadFileName, = struct.unpack("?", f.read(struct.calcsize("?")))
                if IsNextRadFileName:
                    NextRadFileName = read_string(f)
                else:
                    NextRadFileName = None
            else:
                PrevRadFileName = None
                NextRadFileName = None
            if PrevRadFileName is not None:
                if not os.path.exists(PrevRadFileName):
                    PrevRadFileName = None
            if NextRadFileName is not None:
                if not os.path.exists(NextRadFileName):
                    NextRadFileName = None

            #Загрузка радарограммы
            if not OldVersion:
                part_of_file = f.read(struct.calcsize("ffiiff"))
                if Version < 21:
                    dL, TimeBase, TracesCount, SamplesCount, AntDist, DefaultV = struct.unpack("ffiiff", part_of_file)
                    if TimeBase < 1:
                        dL, TimeBase, TracesCount, SamplesCount, AntDist, DefaultV = struct.unpack("fiiiff", part_of_file)
                else:
                    dL, TimeBase, TracesCount, SamplesCount, AntDist, DefaultV = struct.unpack("ffiiff", part_of_file)
            else:
                dL, TimeBase, TracesCount, SamplesCount  = struct.unpack("fiii", f.read(struct.calcsize("fiii")))
                AntDist = 1.0
                DefaultV = 0.1

            if DefaultV > 0.3: DefaultV = 0.3

            if TimeBase <= 0: return None
            AntDist = round(AntDist, 5)
            DefaultV = round(DefaultV, 3)
            dL = round(dL, 5)

            if Version >= 32:
                DataSchemeTracesCount, DataSchemeSamplesCount = struct.unpack("ii", f.read(struct.calcsize("ii")))
                DataScheme = np.fromfile(f, count=DataSchemeTracesCount * DataSchemeSamplesCount)

            if Version != 26:
                DataTrace = np.fromfile(f, count=TracesCount*SamplesCount)
            else:
                decompress = decompressFromFile()
                if decompress is not None:
                    DataTrace = np.copy(np.frombuffer(decompress, count=TracesCount*SamplesCount))
                else:
                    return None
            DataTrace = np.nan_to_num(DataTrace)

            if (Version < 42):
                UnderlaysFileNamesData = None
                UnderlaysFileNamesAttribute = None
            else:
                UnderlaysFileNamesData = []
                UnderlaysFileNamesDataCount, = struct.unpack("i", f.read(struct.calcsize("i")))
                for i in range(UnderlaysFileNamesDataCount):
                    UnderlayFileName = read_string(f)
                    UnderlaysFileNamesData.append(UnderlayFileName)

                UnderlaysFileNamesAttribute = []
                UnderlaysFileNamesAttributeCount, = struct.unpack("i", f.read(struct.calcsize("i")))
                for i in range(UnderlaysFileNamesAttributeCount):
                    UnderlayFileName = read_string(f)
                    UnderlaysFileNamesAttribute.append(UnderlayFileName)

            if (Version >= 9) and (Version < 11):
                DataRad = np.fromfile(f, count=TracesCount * SamplesCount)
            if Version >= 10:
                if Version != 26:
                    GainCoef = np.fromfile(f, count=SamplesCount)
                else:
                    decompress = decompressFromFile()
                    if decompress is not None:
                        GainCoef = np.copy(np.frombuffer(decompress, count=SamplesCount))
                    else:
                        return None
            else:
                GainCoef = None

            if Version >= 17:
                IsGPRUnit, = struct.unpack("?", f.read(struct.calcsize("?")))
                if IsGPRUnit:
                    GPRUnit = read_string(f)
                else:
                    GPRUnit = None

                IsAntenName, = struct.unpack("?", f.read(struct.calcsize("?")))
                if IsAntenName:
                    AntenName = read_string(f)
                else:
                    AntenName = None

                IsFrequency, = struct.unpack("?", f.read(struct.calcsize("?")))
                if IsFrequency:
                    Frequency, = struct.unpack("f", f.read(struct.calcsize("f")))
                else:
                    Frequency = None
            else:
                GPRUnit = None
                AntenName = None
                Frequency = None

            if Version >=16:
                IsParts, = struct.unpack("?", f.read(struct.calcsize("?")))
                if IsParts:
                    n, = struct.unpack("i", f.read(struct.calcsize("i")))
                    NumTraceStarts_ = np.fromfile(f, count=n, dtype="int64")
                    NumTraceFinishs_ = np.fromfile(f, count=n, dtype="int64")

                    m, = struct.unpack("i", f.read(struct.calcsize("i")))
                    SourceFileNames_ = []
                    for i in range(m):
                        SourceFileName = read_string(f)
                        SourceFileNames_.append(SourceFileName)

                    Parts = pd.DataFrame({"NumTraceStarts": NumTraceStarts_, "NumTraceFinishs": NumTraceFinishs_, "NumTraceFinishs": SourceFileNames_})
                else:
                    Parts = None
            else:
                Parts = None

            if Version >= 13:
                IsTimeCollecting, = struct.unpack("?", f.read(struct.calcsize("?")))
                if IsTimeCollecting:
                    if Version <= 27:
                        if Version != 26:
                            TimeCollecting = np.fromfile(f, count=TracesCount, dtype="uint64")
                        else:
                            decompress = decompressFromFile()
                            if decompress is not None:
                                TimeCollecting = np.copy(np.frombuffer(decompress, count=TracesCount, dtype="uint64"))
                            else:
                                TimeCollecting = None
                    else:
                        TimeCollecting = np.fromfile(f, count=TracesCount, dtype="int64")
                else:
                    TimeCollecting = None
            else:
                TimeCollecting = None
            if TimeCollecting is not None:
                TimeCollecting = np.nan_to_num(TimeCollecting)

            if Version < 21:
                if Version >= 14:
                    IsGPStrajectory, = struct.unpack("?", f.read(struct.calcsize("?")))
                    if IsGPStrajectory:
                        n, = struct.unpack("i", f.read(struct.calcsize("i")))
                        X_ = np.fromfile(f, count=n, dtype="float64")
                        Y_ = np.fromfile(f, count=n, dtype="float64")
                        Z_ = [0]*len(X_)
                        DateTime_ = np.fromfile(f, count=n, dtype="uint64")
                        sum_distances_ = np.fromfile(f, count=n, dtype="float64")

                        GPStrajectory = pd.DataFrame({"X": X_, "Y": Y_, "Z": Z_, "DateTime": DateTime_})
                        GPStrajectory["DateTime"] = GPStrajectory["DateTime"].astype("datetime64[ns]")
                    else:
                        GPStrajectory = None
                else:
                    GPStrajectory = None
                IsGeographical = False
                IsByTime = True

                if Version >= 14:
                    IsGPSTraces, = struct.unpack("?", f.read(struct.calcsize("?")))
                    if IsGPSTraces:
                        n, = struct.unpack("i", f.read(struct.calcsize("i")))
                        DateCollecting_ = np.fromfile(f, count=n, dtype="uint64")
                        Latitude_ = np.fromfile(f, count=n, dtype="float64")
                        Longitude_ = np.fromfile(f, count=n, dtype="float64")
                        TimeCollecting_ = np.fromfile(f, count=n, dtype="int64")
                if Version >= 18:
                    IsCoordTraces, = struct.unpack("?", f.read(struct.calcsize("?")))
                    if IsCoordTraces:
                        n, = struct.unpack("i", f.read(struct.calcsize("i")))
                        X_ = np.fromfile(f, count=n, dtype="float64")
                        Y_ = np.fromfile(f, count=n, dtype="float64")
                        Z_ = np.fromfile(f, count=n, dtype="float64")
                CoordTraces = None

            else:
                if Version != 26:
                    X_ = np.fromfile(f, count=TracesCount, dtype="float64")
                    Y_ = np.fromfile(f, count=TracesCount, dtype="float64")
                    Z_ = np.fromfile(f, count=TracesCount, dtype="float64")
                else:
                    decompress = decompressFromFile()
                    if decompress is not None:
                        X_ = np.copy(np.frombuffer(decompress, count=TracesCount, dtype="float64"))
                    else:
                        X_ = None
                    decompress = decompressFromFile()
                    if decompress is not None:
                        Y_ = np.copy(np.frombuffer(decompress, count=TracesCount, dtype="float64"))
                    else:
                        Y_ = None
                    decompress = decompressFromFile()
                    if decompress is not None:
                        Z_ = np.copy(np.frombuffer(decompress, count=TracesCount, dtype="float64"))
                    else:
                        Z_ = None
                if (X_ is None) or (Y_ is None) or (Z_ is None):
                    CoordTraces = None
                else:
                    CoordTraces = pd.DataFrame({"X": X_, "Y": Y_, "Z": Z_})
                if CoordTraces is not None:
                    CoordTraces["X"] = np.nan_to_num(CoordTraces["X"].values)
                    CoordTraces["Y"] = np.nan_to_num(CoordTraces["Y"].values)
                    CoordTraces["Z"] = np.nan_to_num(CoordTraces["Z"].values)

            if Version >= 34:
                PK = np.fromfile(f, count=TracesCount, dtype="float64")
            else:
                PK = None
            if PK is not None:
                PK = np.nan_to_num(PK)

            if Version >= 47:
                SurfaceSamples = np.fromfile(f, count=TracesCount, dtype="int")
            else:
                SurfaceSamples = None
            if SurfaceSamples is not None:
                SurfaceSamples = np.nan_to_num(SurfaceSamples)

            if Version >= 48:
                isZShiftToSurface, = struct.unpack("?", f.read(struct.calcsize("?")))
            else:
                isZShiftToSurface = False

            if Version >= 12:
                IsDataAttribute, = struct.unpack("?", f.read(struct.calcsize("?")))
                if IsDataAttribute:
                    if Version != 26:
                        DataAttribute = np.fromfile(f, count=TracesCount * SamplesCount)
                    else:
                        decompress = decompressFromFile()
                        if decompress is not None:
                            DataAttribute = np.copy(np.frombuffer(decompress, count=TracesCount * SamplesCount))
                        else:
                            DataAttribute = None
                else:
                    DataAttribute = None
            else:
                DataAttribute = None
            if DataAttribute is not None:
                DataAttribute = np.nan_to_num(DataAttribute)

            if Version >= 21:
                IsGeographical, = struct.unpack("?", f.read(struct.calcsize("?")))
                if Version >= 36:
                    IsByTime, = struct.unpack("?", f.read(struct.calcsize("?")))
                else:
                    IsByTime = True
                IsTrajectory, = struct.unpack("?", f.read(struct.calcsize("?")))
                if IsTrajectory:
                    n, = struct.unpack("i", f.read(struct.calcsize("i")))

                    if Version != 26:
                        X_ = np.fromfile(f, count=n, dtype="float64")
                        Y_ = np.fromfile(f, count=n, dtype="float64")
                        Z_ = np.fromfile(f, count=n, dtype="float64")
                        if IsByTime:
                            DateTime_ = np.fromfile(f, count=n, dtype="uint64")
                        else:
                            TraceNumber_ = np.fromfile(f, count=n, dtype="int64")
                    else:
                        decompress = decompressFromFile()
                        if decompress is not None:
                            X_ = np.copy(np.frombuffer(decompress, count=n, dtype="float64"))
                        else:
                            X_ = None
                        decompress = decompressFromFile()
                        if decompress is not None:
                            Y_ = np.copy(np.frombuffer(decompress, count=n, dtype="float64"))
                        else:
                            Y_ = None
                        decompress = decompressFromFile()
                        if decompress is not None:
                            Z_ = np.copy(np.frombuffer(decompress, count=n, dtype="float64"))
                        else:
                            Z_ = None
                        DateTime_ = np.fromfile(f, count=n, dtype="uint64")
                    if (X_ is None) or (Y_ is None) or (Z_ is None):
                        GPStrajectory = None
                    else:
                        if IsByTime:
                            GPStrajectory = pd.DataFrame({"X": X_, "Y": Y_, "Z": Z_, "DateTime": DateTime_})
                            GPStrajectory["DateTime"] = GPStrajectory["DateTime"].astype("datetime64[ns]")
                        else:
                            GPStrajectory = pd.DataFrame({"X": X_, "Y": Y_, "Z": Z_, "TraceNumber": TraceNumber_})
                else:
                    GPStrajectory = None
                    IsGeographical = False
            else:
                GPStrajectory = None
                IsGeographical = False
                IsByTime = True

            DataTrace = np.reshape(DataTrace, (TracesCount, SamplesCount))
            if DataAttribute is not None:
                DataAttribute = np.reshape(DataAttribute, (TracesCount, SamplesCount))

            RadInfo = {"Parts": Parts, "dL": dL, "TimeBase": TimeBase, "DataTrace": DataTrace, "DataAttribute": DataAttribute,
                       "TimeCollecting": TimeCollecting, "CoordTraces": CoordTraces, "SurfaceSamples": SurfaceSamples, "isZShiftToSurface": isZShiftToSurface,
                       "PK": PK, "GainCoef": GainCoef, "AntDist": AntDist, "DefaultV": DefaultV,
                       "GPRUnit": GPRUnit, "AntenName": AntenName, "Frequency": Frequency,
                       "UnderlaysFileNamesData": UnderlaysFileNamesData, "UnderlaysFileNamesAttribute": UnderlaysFileNamesAttribute}
            TrajectoryInfo = {"IsGeographical": IsGeographical, "GPStrajectory": GPStrajectory}

            # #Загрузка внешних графиков
            # if Version < 35:
            #     ExternalPlotsCharts = None
            # else:
            #     n, = struct.unpack("i", f.read(struct.calcsize("i")))
            #     data = f.read(n)
            #     ExternalPlotsCharts = pickle.loads(data)
            # ExternalPlotsInfo = {"Charts": ExternalPlotsCharts}
            #
            # #Загрузка слоев
            # LayersCount, = struct.unpack("i", f.read(struct.calcsize("i")))
            # LayersInfo = []
            # for i in range(LayersCount):
            #     if Version < 44:
            #         caption = read_string(f, 200)
            #         color = read_string(f, 200)
            #     else:
            #         caption = read_string(f)
            #         color = read_string(f)
            #     visible, = struct.unpack("?",f.read(struct.calcsize("?")))
            #     if Version >= 45:
            #         blocked, = struct.unpack("?", f.read(struct.calcsize("?")))
            #     else:
            #         blocked = False
            #     if Version >= 49:
            #         order, = struct.unpack("i", f.read(struct.calcsize("i")))
            #     else:
            #         order = 0
            #     if Version >= 44:
            #         memo = read_string(f)
            #     else:
            #         memo = ""
            #
            #     if Version >= 22:
            #         isGroundLayer, = struct.unpack("?",f.read(struct.calcsize("?")))
            #         if isGroundLayer:
            #             n, = struct.unpack("i", f.read(struct.calcsize("i")))
            #             intervals_ = np.fromfile(f, count=n, dtype="float64")
            #             colors_ = np.fromfile(f, count=n, dtype="int32")
            #             Intervals = pd.DataFrame({"intervals": intervals_, "colors": colors_})
            #         else:
            #             Intervals = pd.DataFrame({"intervals": [], "colors": []})
            #     else:
            #         isGroundLayer = False
            #         Intervals = pd.DataFrame({"intervals": [], "colors": []})
            #
            #     LayersInfo.append({"caption": caption, "color": color, "visible": visible, "blocked": blocked, "order": order,
            #                        "memo": memo, "isGroundLayer": isGroundLayer, "Intervals": Intervals})
            # if Version < 43:
            #     currlayer_caption = "DEFAULT"
            # else:
            #     currlayer_caption = read_string(f)
            #
            # LayersModel = None
            # if Version >= 33:
            #     isLayersModel, = struct.unpack("?", f.read(struct.calcsize("?")))
            #     if isLayersModel:
            #         n, = struct.unpack("i", f.read(struct.calcsize("i")))
            #         data = f.read(n)
            #         LayersModel = pickle.loads(data)
            #     else:
            #         LayersModel = None
            # if Version < 40:
            #     LayersModel = None
            #
            # #Загрузка элементов
            # ElementsCount, = struct.unpack("i", f.read(struct.calcsize("i")))
            # ElementsInfo = []
            # for i in range(ElementsCount):
            #     if Version < 44: length = 200
            #     else: length = 256
            #
            #     caption = read_string(f, length)
            #     layer, colorByLayer = struct.unpack("i?",f.read(struct.calcsize("i?")))
            #     color = read_string(f, length)
            #     visible, = struct.unpack("?",f.read(struct.calcsize("?")))
            #
            #     if Version >= 45:
            #         blocked, = struct.unpack("?",f.read(struct.calcsize("?")))
            #     else:
            #         blocked = False
            #     k, = struct.unpack("i",f.read(struct.calcsize("i")))
            #
            #     color = change_color(color)
            #     L0 = None
            #     T0 = None
            #     T0_s = None
            #     L1 = None
            #     T1 = None
            #     V = None
            #     VBorder = None
            #     dL = None
            #     H = None
            #     AntDist = None
            #     beta = None
            #     offset = None
            #     Vertexes = []
            #     height = None
            #     L = None
            #     count = None
            #     T = None
            #     LayersCaption = None
            #     vertexes_all = None
            #
            #     if k==1:
            #         kind = "точка"
            #         L0, T0 = struct.unpack("ff",f.read(struct.calcsize("ff")))
            #         L0 = round(L0, 5)
            #         T0 = round(T0, 5)
            #     elif k==2:
            #         kind = "отрезок"
            #         L0, T0, L1, T1 = struct.unpack("ffff",f.read(struct.calcsize("ffff")))
            #         L0 = round(L0, 5)
            #         T0 = round(T0, 5)
            #         L1 = round(L1, 5)
            #         T1 = round(T1, 5)
            #     elif k==3:
            #         kind = "гипербола"
            #         L0, T0, V, dL = struct.unpack("ffff",f.read(struct.calcsize("ffff")))
            #         L0 = round(L0, 5)
            #         T0 = round(T0, 5)
            #         V = round(V, 5)
            #         dL = round(dL, 5)
            #     elif k==4:
            #         kind = "ломаная"
            #         VBorder, = struct.unpack("f",f.read(struct.calcsize("f")))
            #         VertexesCount, = struct.unpack("i", f.read(struct.calcsize("i")))
            #         if Version < 41:
            #             for j in range(VertexesCount):
            #                 x = struct.unpack("f",f.read(struct.calcsize("f")))
            #                 y = struct.unpack("f",f.read(struct.calcsize("f")))
            #                 Vertexes.append([x[0],y[0]])
            #             Vertexes = np.array(Vertexes)
            #         else:
            #             Vertexes = np.fromfile(f, count=VertexesCount*2)
            #             Vertexes = np.reshape(Vertexes, (VertexesCount, 2))
            #         if Version >= 30:
            #             vertexes_all = np.fromfile(f, count=TracesCount)
            #             if Version < 41:
            #                 vertexes_all = None
            #         else:
            #             vertexes_all = None
            #         if len(Vertexes) == 0: continue
            #         Vertexes = Vertexes[np.argsort(Vertexes[:, 0])]
            #         Vertexes = Vertexes[np.unique(Vertexes[:, 0], return_index=True)[1]]
            #     elif k==5:
            #         kind = "диффгипербола"
            #         L0, H, V, dL, AntDist = struct.unpack("fffff",f.read(struct.calcsize("fffff")))
            #         L0 = round(L0, 5)
            #         H = round(H, 5)
            #         V = round(V, 5)
            #         dL = round(dL, 5)
            #         AntDist = round(AntDist, 5)
            #     elif k==6:
            #         kind = "смещгипербола"
            #         L0, T0, offset, L1, T1, V, beta, H = struct.unpack("ffffffff",f.read(struct.calcsize("ffffffff")))
            #         L0 = round(L0, 5)
            #         T0 = round(T0, 5)
            #         offset = round(offset, 5)
            #         L1 = round(L1, 5)
            #         T1 = round(T1, 5)
            #         V = round(V, 5)
            #         beta = round(beta, 5)
            #         H = round(H, 5)
            #     elif k==7:
            #         kind = "ACгодограф"
            #         L0, T0_s, V, T0, dL = struct.unpack("fffff",f.read(struct.calcsize("fffff")))
            #         L0 = round(L0, 5)
            #         T0_s = round(T0_s, 5)
            #         V = round(V, 5)
            #         T0 = round(T0, 5)
            #         dL = round(dL, 5)
            #     elif k==8:
            #         kind = "текст"
            #         L0, T0, height = struct.unpack("ffi",f.read(struct.calcsize("ffi")))
            #         L0 = round(L0, 5)
            #         T0 = round(T0, 5)
            #     elif k==9:
            #         kind = "прямоугольник"
            #         L0, T0, L1, T1 = struct.unpack("ffff",f.read(struct.calcsize("ffff")))
            #         L0 = round(L0, 5)
            #         T0 = round(T0, 5)
            #         L1 = round(L1, 5)
            #         T1 = round(T1, 5)
            #     elif k == 10:
            #         kind = "скважина"
            #         L, AntDist = struct.unpack("ff", f.read(struct.calcsize("ff")))
            #         L = round(L, 5)
            #         AntDist = round(AntDist, 5)
            #         count, = struct.unpack("i", f.read(struct.calcsize("i")))
            #         H = np.fromfile(f, count=count)
            #         T = np.fromfile(f, count=count)
            #         V = np.fromfile(f, count=count)
            #         if Version < 24:
            #             H = np.insert(H,0,0)
            #             H = H[1:]-H[:-1]
            #
            #         if Version >= 24:
            #             T0, = struct.unpack("f", f.read(struct.calcsize("f")))
            #         else:
            #             T0 = 0
            #         LayersCaption = []
            #         for j in range(count):
            #             length = 200 if Version < 43 else 256
            #             layerCaption = read_string(f, length)
            #             LayersCaption.append(layerCaption)
            #     else:
            #         continue
            #
            #     ElementsInfo.append({"caption": caption, "layer": layer, "colorByLayer": colorByLayer, "color": color,
            #                          "visible": visible, "blocked": blocked,
            #                          "kind": kind, "L0": L0, "T0": T0, "T0_s": T0_s, "L1": L1, "T1": T1, "V": V, "dL": dL,
            #                          "Vertexes": Vertexes, "vertexes_all": vertexes_all, "H": H, "AntDist": AntDist,
            #                          "offset": offset, "beta": beta, "VBorder": VBorder, "height": height,
            #                          "L": L, "T": T, "LayersCaption": LayersCaption})
            #
            # #Загрузка параметров грунтовой модели
            # GroundModelInfo = None
            # IsModel, = struct.unpack("?",f.read(struct.calcsize("?")))
            # if IsModel:
            #     AxePosition, LayerNum, Transform, InstantlyHodCalc = struct.unpack("fi??",f.read(struct.calcsize("fi??")))
            #
            #     ModelCount, = struct.unpack("i",f.read(struct.calcsize("i")))
            #     Model = []
            #     S = 0
            #     for i in range(ModelCount):
            #         layer = {}
            #         if Version>=4:
            #             layer['H'], layer['D'], layer['V'], layer['eps'], layer['Vef'], layer['t'], layer['Vkrot_god'], layer['Vkrot_layer'] = struct.unpack("ffffffff",f.read(struct.calcsize("ffffffff")))
            #         else:
            #             layer['H'], layer['V'], layer['eps'], layer['Vef'], layer['t'], layer['Vkrot_god'] = struct.unpack("ffffff",f.read(struct.calcsize("ffffff")))
            #             S = S + layer['H']
            #             layer['D'] = S
            #             layer['Vkrot_layer'] = layer['V']*50
            #         Model.append(layer)
            #
            #     NewModelCount, = struct.unpack("i",f.read(struct.calcsize("i")))
            #     NewModel = []
            #     for i in range(NewModelCount):
            #         layer = {}
            #         layer['H'], layer['V'] = struct.unpack("ff",f.read(struct.calcsize("ff")))
            #         NewModel.append(layer)
            #     GroundModelInfo = {"AxePosition": AxePosition, "LayerNum": LayerNum, "Transform": Transform,
            #                         "InstantlyHodCalc": InstantlyHodCalc, "Model": Model, "NewModel": NewModel}
            #
            # #Загрузка параметров привязки
            # if (Version >= 21) and (Version != 26):
            #     try:
            #         IsPopBinding, = struct.unpack("?",f.read(struct.calcsize("?")))
            #         if IsPopBinding:
            #             V,a = struct.unpack("ff",f.read(struct.calcsize("ff")))
            #             if Version != 26:
            #                 Vtraces = np.fromfile(f, count=TracesCount, dtype="float64")
            #             else:
            #                 Vtraces = np.copy(np.frombuffer(decompress, count=TracesCount, dtype="float64"))
            #             IsIncline,IsBorders = struct.unpack("??",f.read(struct.calcsize("??")))
            #             IsSimple, IsAmplitudeAnalysis = struct.unpack("??", f.read(struct.calcsize("??")))
            #             TimeDelta,  = struct.unpack("f", f.read(struct.calcsize("f")))
            #
            #             if Version >= 23:
            #                 IsLevel,  = struct.unpack("?", f.read(struct.calcsize("?")))
            #             else:
            #                 IsLevel = True
            #
            #             if Version < 29:
            #                 isDataSimple = False
            #                 x,y,z = struct.unpack("iii",f.read(struct.calcsize("iii")))
            #                 if Version != 26:
            #                     PopBindingData = np.fromfile(f, count=x * y * z)
            #                 else:
            #                     PopBindingData = np.copy(np.frombuffer(decompressFromFile(), count=x * y * z))
            #                 PopBindingData = np.reshape(PopBindingData, (x, y, z))
            #                 PopBindingSimpleData = None
            #             else:
            #                 isDataSimple, = struct.unpack("?", f.read(struct.calcsize("?")))
            #                 if not isDataSimple:
            #                     x, y, z = struct.unpack("iii", f.read(struct.calcsize("iii")))
            #                     PopBindingData = np.fromfile(f, count=x * y * z)
            #                     PopBindingData = np.reshape(PopBindingData, (x, y, z))
            #                     PopBindingSimpleData = None
            #                 else:
            #                     PopBindingSimpleData = np.fromfile(f, count=TracesCount * SamplesCount)
            #                     PopBindingSimpleData = np.reshape(PopBindingSimpleData, (TracesCount, SamplesCount))
            #                     PopBindingData = None
            #
            #             if Version >= 26:
            #                 isDataVisual,  = struct.unpack("?", f.read(struct.calcsize("?")))
            #             else:
            #                 isDataVisual = True
            #
            #             if isDataVisual:
            #                 x, = struct.unpack("i", f.read(struct.calcsize("i")))
            #                 if Version != 26:
            #                     L_visual = np.fromfile(f, count=x)
            #                 else:
            #                     L_visual = np.copy(np.frombuffer(decompressFromFile(), count=x))
            #                 x, = struct.unpack("i", f.read(struct.calcsize("i")))
            #                 if Version != 26:
            #                     H_visual = np.fromfile(f, count=x)
            #                 else:
            #                     H_visual = np.copy(np.frombuffer(decompressFromFile(), count=x))
            #                 x,y = struct.unpack("ii", f.read(struct.calcsize("ii")))
            #                 if Version != 26:
            #                     Data_visual = np.fromfile(f, count=x * y)
            #                 else:
            #                     Data_visual = np.copy(np.frombuffer(decompressFromFile(), count=x * y))
            #                 Data_visual = np.reshape(Data_visual, (x, y))
            #             else:
            #                 L_visual = None
            #                 H_visual = None
            #                 Data_visual = None
            #
            #             PopBindingInfo = {'FileName': FileName, 'V': V, 'a': a, 'Vtraces': Vtraces,
            #                               'IsIncline': IsIncline, 'IsBorders': IsBorders, 'IsSimple': IsSimple, 'IsAmplitudeAnalysis': IsAmplitudeAnalysis,
            #                               'TimeDelta': TimeDelta, 'IsLevel': IsLevel, 'isDataSimple': isDataSimple,
            #                               'PopBindingData': PopBindingData, 'PopBindingSimpleData': PopBindingSimpleData,
            #                               'isDataVisual': isDataVisual, 'L_visual': L_visual, 'H_visual': H_visual, 'Data_visual': Data_visual}
            #         else:
            #             PopBindingInfo = None
            #     except:
            #         PopBindingInfo = None
            # else:
            #     PopBindingInfo = None

        # return FileName, RadInfo, TrajectoryInfo, ExternalPlotsInfo, LayersInfo, currlayer_caption, LayersModel, ElementsInfo, GroundModelInfo, \
        #        PopBindingInfo, PrevRadFileName, NextRadFileName, Notes, HistoryCaptions
        #
        return FileName, RadInfo, TrajectoryInfo, PrevRadFileName, NextRadFileName, Notes, HistoryCaptions
    except UnicodeError: #TODO убрать
        return None
