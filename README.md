# Senj
[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/kalituma/senj/blob/main/README.en.md) 

- Yaml 기반 Snap 및 GDAL 전처리 라이브러리
- Senj에 포함된 대기보정 프로세서는 acolite를 구성하는 소스 코드를 활용하였습니다.  (https://github.com/acolite/acolite).
- being developed by kalituma and Curious_Coldbrew at AIRS lab., PKNU

---

## 필요 패키지
- gdal, cv2, jsonpath_ng, pyyaml, scipy, matplotlib, lxml, 
requests, pyresample, pyhdf, netCDF4, tqdm, scikit-image,
cerberus, networkx

---

## 필요 프로그램
- snap(esa-snappy)

---
## 전처리 라이브러리 실행

- 전처리 모듈은 사용자가 작성한 YAML Configuration 파일을 읽어 전처리를 수행합니다.
- 전처리 모듈 실행을 위한 python script는 LIBRARY/senj/execute/run_config.py 입니다.
- python script의 옵션은 --config_path, --log_dir, --log_level이 있습니다
- --config_path는 사용자가 작성한 YAML Configuration 파일의 경로를 나타냅니다.
- --log_dir는 로그 파일을 저장할 디렉토리 경로를 나타냅니다.
- --log_level은 출력을 위한 로그 레벨을 나타냅니다. (DEBUG, INFO, WARNING, ERROR, CRITICAL)

```bash
python path/to/run_config.py --config_path 'path/to/config.yaml' --log_dir 'path/to/log' --log_level 'DEBUG'
```
---

## YAML 작성 방법

- YAML은 들여쓰기를 사용하여 전처리 절차를 계층적으로 표현합니다.
- 전처리를 위한 YAML을 구성하는 개념적 요소는 processor, operation으로 구성됩니다.
- processor는 operation을 포함하는 전처리 과정의 하나의 단위로, input, operations 등의 항목을 __필수적으로__ 포함합니다.
- processor의 이름은 사용자의 목적에 맞게 정의될 수 있습니다.
- 앞에서 정해진 processor의 이름은 이후 등장하는 processor의 input 항목에 사용되어 processor 간의 연결을 위해 사용됩니다.
- operation은 processor 내에서 데이터를 처리하는 단위로, 'read', 'write' 등 약속된 이름이 정의되어 있습니다.

```yaml
processor_1: # processor 이름 수정 가능
  input:
    ... 
  operations: [read, resample, ...] # operation 이름 수정 불가
  read:  
    ...
  resample:
    ...

processor_2:
  input:
    path: '{{processor_1}}' # processor_1의 출력 자료를 사용한다는 의미
  operations:
    [subset, select, ...]
  subset:
    ...
  select:
    ...
```

- ### Input

  - input 항목은 processor의 입력 데이터를 정의합니다.
  - input 항목은 path, pattern, sort 등의 항목을 포함할 수 있습니다.
  - path는 입력 데이터의 경로를 나타내며, 파일 경로, 디렉토리 경로, processor link 등을 사용할 수 있습니다.  
  

    
```yaml
processor_1:
  input:
    path: 'path/to/file1' # 한 개의 파일 경로를 사용
```
- 여러 개의 파일 경로는 리스트 형태로 사용합니다.
```yaml
processor_1:
    input:
      path: ['path/to/file1', 'path/to/file2', ...] # 여러 개의 파일 경로를 사용
```

- 디렉토리 경로의 경우, pattern과 sort 항목을 사용할 수 있습니다.
- pattern은 디렉토리 내의 파일 중 특정 패턴을 가진 파일만 사용할 때 사용합니다. (glob 패턴 사용)
- sort는 설정된 디렉토리 내에서 pattern을 가진 파일 불러 왔을 경우, 불러온 파일들을 정렬할 때 사용합니다
- sort의 func에 ___'!{함수 이름}'___ 형식으로 정렬 함수를 지칭할 수 있습니다.
- LIBRARY/senj/core.lambda_funcs.sort_lambda.py에 정의된 함수를 사용하거나 직접 함수를 정의하여 사용할 수 있습니다.
```yaml
processor_1:
  input:
    path: 'path/to/dir' # 디렉토리 경로를 사용
    pattern: '*.tif' # 디렉토리 내의 파일 중 특정 패턴(예: tif 확장자)을 가진 파일만 사용
    sort:
      func: '!{sort_by_something}' # 파일 정렬 방법을 사용
```

- sort의 func 사용할 함수를 정의할 때는 lambda 객체에 등록하여 사용합니다

```python
@LAMBDA.reg(name='sort_by_something') #  함수를 lambda에 등록, 여기서 사용된 'sort_by_something'은 sort 항목의 func에 사용됨 
def sort_by_last_number(file_name: str) -> int:
    return int(Path(file_name).stem.split('_')[-1]) # xxx_xxx_1.tif 형태로 구성된 파일에서 마지막 숫자를 기준으로 정렬
```

- processor link는 다른 processor의 출력 데이터를 사용할 때 사용합니다.
- processor link는 ___'{{processor_name}}'___ 형태로 사용합니다.
```yaml
processor_1:
    ...
processor_2:
    input:
      path: '{{processor_1}}' # 한 개의 link를 사용
```

- 여러 개의 processor link를 사용할 때는 리스트 형태로 사용합니다.
```yaml
processor_1:
    ...
processor_2:
    ...
processor_3:
    input:
      path: ['{{processor_1}}', '{{processor_2}}'] # 여러 개의 link를 사용
```

---


## Operations 

| Operation Name |          Available Product type           |                                                                                arguments                                                                                 |   module   |                    description                    |
|:--------------:|:-----------------------------------------:|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|:----------:|:-------------------------------------------------:|
|      read      |                    All                    |                                             ___module(str)___, bands(list[int, str]), bword(str), bname_word_included(bool)                                              | gdal, snap |                                                   |          
|     write      |                    All                    |                                     ___out_dir(str)___, out_stem(str), out_ext(str), bands(list[int, str]), prefix(str), suffix(str)                                     | gdal, snap |                                                   |
|    convert     |                    All                    |                                                                           ___to_module(str)___                                                                           | gdal, snap |                                                   |
|    resample    |                    All                    |                                                           epsg(int), pixel_size(float), resampling_method(str)                                                           | gdal, snap |           epsg 혹은 pixel_size 둘 중 하나는 필수           |
|     subset     |                    All                    |                                                               ___bounds(list[float])___, bounds_espg(int)                                                                | gdal, snap |                                                   |
|     select     |                    All                    |                                                              bands(list[int, str]), band_labels(list[str])                                                               | gdal, snap |          band 혹은 band_labels 둘 중 하나는 필수           |
|     mosaic     |                    All                    |                                                             ___master_module(str)___, bands(list[str, int])                                                              | gdal, snap |              snap module의 경우, 개선 필요               |
|     stack      |                    All                    |                                                                   band_list(list[list[int,str], None])                                                                   | gdal, snap |                                                   |
|atmos_corr | Sentinel-2, WorldView/GeoEye, PlanetScope | ___bands___[List[str, int]], ___band_slots___(List[str]), write_map(bool), map_dir(str), map_stem(str), det_bnames(List[str]), det_bword_include(bool), det_pattern(str) | gdal, snap | det_bnames 혹은 det_bword_include, det_pattern 중 선택 |
| nl_mean_denoising|                    All                    |                                              bands(List[int,str]), h(float), templateWindowSize(int), searchWindowSize(int)                                              | gdal, snap |                                                   |
| apply_orbit| Sentinel-1 |                                                        orbit_type(str), poly_degree(int), continue_on_fail(bool)                                                         | snap |
| calibrate| Sentinel-1 |                     polarizations(List[str]), output_sigma(bool), output_beta(bool), output_gamma(bool), output_in_db(bool), output_in_complex(bool)                     |snap||
| terrain_correction| Sentinel-1 |        bands(List[str, int]), dem_name(str), pixel_spacing_meter(float), pixel_spacing_degree(float), dem_method(str), img_method(str), save_dem(bool), epsg(int)        |snap||
| speckle_filter| Sentinel-1 | bands(List[str, int]), filter(str), dampling_factor(int), filter_size(list[int]), number_looks(int), window_size(str), target_window_size(str), sigma(str), an_size(int)|snap||
|thermal_noise_removal| Sentinel-1 | polarizations(List[str])|snap||
|topsar_deburst| Sentinel-1 | polarizations(List[str])|snap||

* arguments의 ___강조 및 기울여진 항목___ 은 필수 argument을 의미

- ### Read
- read는 입력 데이터를 읽어오는 operation으로 processor를 구성하는 operations list의 첫번째에 포함될 수 있습니다.
- read에서 module은 데이터를 핸들링할 때 사용하는 모듈을 나타내며 gdal, snap 중 하나를 사용할 수 있습니다.
- bands는 읽어올 band의 이름 혹은 인덱스 나타내며, 리스트 형태로 입력합니다.
- bword는 band 이름에 포함된 단어의 패턴(glob 패턴)을 나타내며, bname_word_included가 True를 입력할 경우 band 이름에 bword가 포함된 band만 읽어옵니다.
- bands 혹은 bword 중 하나를 선택해서 사용할 수 있으며 늘 bands가 bword를 우선 합니다.
- bands의 default 값은 전체 밴드(None), bword의 default 값은 *, bname_word_included의 default 값은 False입니다.
   

- Read 예:
```yaml
processor_1:
  operations: [read, ...]
  read:
    module: 'gdal' # gdal, snap 중 하나
    bands: [1, 2, 3] # 읽어올 band    
...
```
```yaml
processor_1:
  operations: [read, ...]
  read:
    module: 'gdal' # gdal, snap 중 하나
    bands: ['B01', 'B02', 'B03'] # 읽어올 band
...
```
```yaml
processor_1:
  operations: [read, ...]
  read:
    module: 'gdal' # gdal, snap 중 하나
    bword: '*B01*' # band 이름에 B01이 포함된 band만 읽어옴
    bname_word_included: True # band 이름에 B01이 포함된 band만 읽어옴
...
```

- ### Write
- write는 전처리 결과를 디스크에 저장하는 operation으로 processor를 구성하는 operations list의 마지막에 포함될 수 있습니다.
- write에서 out_dir은 저장할 디렉토리 경로를 나타내며, out_stem은 저장할 파일 이름의 stem을 나타냅니다.
- out_ext는 저장할 파일의 확장자를 나타내며, bands는 저장할 band의 이름 혹은 인덱스를 나타냅니다.
- prefix는 파일 이름 앞에 붙일 문자열을 나타내며, suffix는 파일 이름 뒤에 붙일 문자열을 나타냅니다.
- out_stem의 default 값은 'out', out_ext의 default 값은 앞서 전달된 데이터의 module에 따라 달라집니다.
  - 지정하지 않을 경우, gdal은 __tif__, snap은 __dim__ 으로 설정되며, 설정할 경우, gdal은 __tif__, snap은 __dim,tif__ 로 설정 가능합니다.)
- bands의 default 값은 전체 밴드(None), prefix와 suffix의 default 값은 ''입니다.
- 입력된 dir, stem, ext, prefix, suffix 및 디렉토리 입려의 경우, 데이터의 전처리 반복 횟수(count) 조합하여 최종 파일 이름을 생성합니다.
- 예 ) out_dir='path/to/dir', out_stem='out', out_ext='tif', prefix='pre', suffix='suf', count=1 -> 'path/to/dir/pre_out_suf.1.tif'
   

- Write 예:
```yaml
processor_1:
  operations: [..., write]
  ...
  write:
    out_dir: 'path/to/dir' # 저장할 디렉토리 경로
    out_stem: 'out' # 저장할 파일 이름의 stem
    out_ext: 'tif' # 저장할 파일의 확장자
    bands: [1, 2, 3] # 저장할 band
    prefix: 'pre' # 파일 이름 앞에 붙일 문자열
    suffix: 'suf' # 파일 이름 뒤에 붙일 문자열
```

- ### Convert
- convert는 데이터를 다른 형식으로 변환하는 operation으로 선행 operation의 module을 다른 module로 바꿔주는 역할을 합니다.
  - 예) gdal -> snap, snap -> gdal
- convert에서 to_module은 변환할 모듈을 나타내며, gdal, snap 중 하나를 사용할 수 있습니다.
   

- convert 예:
```yaml
processor_1:
  operations: [read, convert, ...]
  read:
    module: 'gdal' # gdal, snap 중 하나
    bands: [1, 2, 3] # 읽어올 band
  convert:
    to_module: 'snap' # 변환할 모듈, 이후 operation으로 전달되는 데이터는 snap 모듈 객체가 전달됨
...
``` 

- ### Resample
- resample은 데이터를 다른 해상도 혹은 다른 좌표계로 변환하는 operation입니다.
- resample에서 epsg는 변환할 좌표계의 epsg 코드를 나타내며, pixel_size는 변환할 해상도를 나타냅니다.
- resampling_method는 변환할 때 사용할 resampling 방법을 나타내며 선행 operation이 전달한 데이터의 모듈 종류에 따라 달라질 수 있습니다.
  - gdal의 경우, resampling_method는 __'nearest', 'bilinear', 'bicubic', 'cubicspline', 'lanczos'__ 중 하나를 사용할 수 있습니다.
  - snap의 경우, resampling_method는 __'nearest', 'bilinear', 'bicubic'__ 중 하나를 사용할 수 있습니다.
- epsg 혹은 pixel_size 둘 중 하나는 필수입니다.
- epsg code는 https://epsg.io/ 에서 확인 가능합니다.
   

- Resample 예:
```yaml
processor_1:
  operations: [..., resample, ...]
  ...
  resample:
    epsg: 4326 # 변환할 좌표계의 epsg 코드
    pixel_size: 0.01 # 변환할 해상도
    resampling_method: 'nearest' # 변환할 때 사용할 resampling 방법
...
```
- ### Subset
- subset은 데이터를 특정 영역으로 자르는 operation입니다.
- subset에서 bounds는 자를 영역의 좌표를 나타내며, bounds_epsg는 bounds의 좌표계를 나타냅니다.
- bounds는 [min_x, max_y, max_x, min_y] 형태로 입력하며, bounds_epsg는 좌표계의 epsg 코드를 나타냅니다.
- bounds_epsg의 default 값은 4326입니다.
   

- Subset 예:
```yaml
processor_1:
  operations: [..., subset, ...]
  ...
  subset:
    bounds: [126.5, 38.5, 127.0, 38.0] # 자를 영역의 좌표
    bounds_epsg: 4326 # 좌표계의 epsg 코드
...
```

- ### Select
- select는 데이터의 band만 선택하거나, band의 이름을 변경하는 operation입니다.
- bands는 선택할 band의 이름 혹은 인덱스를 나타내며, 리스트 형태로 입력합니다.
- band_labels는 변환 band의 이름을 나타내며, 리스트 형태로 입력합니다.
- bands 혹은 band_labels 둘 중 하나는 필수입니다.
- band_labels를 사용할 경우, bands의 개수와 동일한 개수의 band_labels를 입력해야 합니다.
   

- Select 예:
```yaml
processor_1:
  operations: [..., select, ...]
  ...
  select:
    bands: ['B2', 'B3', 'B4'] # 선택할 밴드
    band_labels: ['Blue', 'Green', 'Red'] # 밴드의 변경하고자 하는 이름
...
```

- ### Mosaic
- mosaic은 여러 개의 영상을 x,y 축을 기준으로 하나로 합치는 operation이며, 여러 개의 processor의 결과를 list로 합쳐 하나의 processor 결과로 만들 수 있습니다. 
- mosaic에서 master_module은 모자이크를 수행 할 module을 나타내는 필수 argument이며, gdal을 사용할 수 있습니다.
  - snap의 경우, 아직 개선이 필요하며 추후 지원 예정입니다.
- bands는 합칠 band의 이름 혹은 인덱스를 나타내며, 리스트 형태로 입력합니다.
   

- Mosaic 예:
```yaml
processor_1:
  ...
processor_2:
  ...
processor_3:
  input:
    path: ['{{processor_1}}', '{{processor_2}}'] # processor_1, processor_2의 결과를 사용
  operations: [mosaic, ...]
  ...
  mosaic:
    master_module: 'gdal' # 모자이크를 수행할 module
    bands: ['B2', 'B3', 'B4'] # 합칠 밴드
...
```

- ### Stack
- stack은 여러 개의 영상을 z 축을 기준으로 하나로 합치는 operation, 여러 개의 processor의 결과를 list로 합쳐 하나의 processor 결과로 만들 수 있습니다.
- stack에서 band_list는 합칠 band의 이름 혹은 인덱스를 나타내며, 리스트 형태로 입력합니다.
- 합치고자 하는 band가 특정 영상의 전체 밴드일 경우, None을 입력합니다.
- band_list의 default 값은 None입니다.
- master_module은 stack을 수행할 module을 나타내며, gdal, snap을 사용할 수 있습니다.
- meta_from은 stack 결과 데이터로 가져올 메타데이터를 제공할 수 있는 입력된 processor link의 이름을 나타내며, input에 입력된 processor link 중 하나를 사용합니다.
- geo_err는 stack을 수행할 때, 각 밴드가 지리적(bounds, pixel_size)으로 일치하는지 확인하게 되는데, 이때 허용할 수 있는 resolution의 오차를 나타냅니다.
  - geo_err의 default 값은 0.0001입니다.
  

- Stack 예:

```yaml
processor_1:
  ...
processor_2:
  ...
processor_3:
  ...

processor_4:
  input:
    path: ['{{processor_1}}', '{{processor_2}}', '{{processor_2}}'] # processor_1, processor_2의 결과를 사용
  operations: [stack, ...]
    ...
  stack:
    master_module: 'gdal' # stack을 수행할 module
    band_list: [['Red', 'Green', 'Blue'], None, [1, 2, 3]] # 합칠 밴드
    meta_from: '{{processor_1}}' # stack 결과 데이터로 가져올 메타데이터를 제공할 processor link
    geo_err: 0.0001 # 지리적 오차      
```

- ### atmos_corr
- atmos_corr은 optical product의 대기 보정을 수행하는 operation입니다.
- 현재 Sentinel-2, WorldView/GeoEye, PlanetScope을 지원합니다.
- bands는 대기 보정을 수행할 band의 이름 혹은 인덱스를 나타내며, 리스트 형태로 입력합니다.
- band_slots는 대기 보정을 수행할 band의 물리 밴드 slot을 정의하는데 활용되며, 리스트 형태로 입력합니다.
  - Sentinel-2의 경우, band_slots는 ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12']중 골라서 사용합니다.
  - WorldView의 경우, band_slots는 ['coastal', 'blue', 'green', 'yellow', 'red', 'rededge', 'nir1', 'nir2', 'pan']중 골라서 사용합니다.
  - GeoEye의 경우, band_slots는 ['pan', 'blue', 'green', 'red', 'nir']중 골라서 사용합니다.
  - PlanetScope의 경우, band_slots는 ['blue', 'green', 'red', 'nir']중 골라서 사용합니다.
- write_map는 대기 보정 결과를 이미지로 저장할 지 여부를 나타내며 default는 False입니다.
- map_dir은 이미지를 저장할 경우, 저장할 디렉토리 경로를 나타내며, map_stem은 저장할 이미지의 파일 stem을 나타냅니다.
- det_bnames는 영상 detector 번호와 관련된 정보를 저장하고 있는 band 이름을 나타내며, 리스트 형태로 입력합니다.(Sentinel-2 영상에만 해당)
  - Senitnel-2 영상의 경우, 영상의 detector 번호에 따라 solar zenith angle, solar azimuth angle, view zenith angle, view azimuth angle 등이 달라지게 되는데 이를 이용해 센서 관련 파라미터를 얻기 위한 수단으로 해당 argument를 활용
- det_bword_include는 detector 번호 정보를 가진 band를 단어의 패턴을 이용해 조회하고자 할 경우, 활용되며, True, False로 설정합니다.
- det_pattern은 detector 번호 정보를 가진 band를 조회할 때 사용하는 패턴(glob 패턴)을 나타내며, 문자열로 입력합니다.
- det_bnames 혹은 det_bword_include, det_pattern 중 하나를 활용하며, det_bnames가 우선합니다.

   
- atmos_corr 예:
```yaml
# sentinel-2의 경우,
processor_1: 
  operations: [..., atmos_corr, ...]
  ...
  atmos_corr:
    bands: [2, 3, 4] # 대기 보정을 수행할 밴드
    band_slots: ['B2', 'B3', 'B4'] # 대기 보정을 수행할 밴드의 물리 밴드 slot
    write_map: True # 대기 보정 결과를 이미지로 저장할 지 여부
    map_dir: 'path/to/dir' # 이미지를 저장할 디렉토리 경로
    map_stem: 'sentinel2_corrected' # 이미지의 파일 stem    
    det_bword_include: True # detector 번호 정보를 가진 band를 단어의 패턴을 이용해 조회
    det_pattern: 'B_detector*' # detector 번호 정보를 가진 band를 조회할 때 사용하는 패턴
```

```yaml
# PlanetScope의 경우,
processor_1: 
  operations: [..., atmos_corr, ...]
  ...
  atmos_corr:
    bands: ['band_1', 'band_2', 'band_3', 'band_4'] # 대기 보정을 수행할 밴드
    band_slots: ['blue', 'green', 'red', 'nir'] # 대기 보정을 수행할 밴드의 물리 밴드 slot
    write_map: True # 대기 보정 결과를 이미지로 저장할 지 여부
    map_dir: 'path/to/dir' # 이미지를 저장할 디렉토리 경로
    map_stem: 'planet_corrected' # 이미지의 파일 stem
```

- ### nl_mean_denoising
- nl_mean_denoising은 opencv의 fastNlMeansDenoising 함수를 활용해 영상의 노이즈를 제거하는 operation입니다.
- bands는 노이즈 제거를 수행할 band의 이름 혹은 인덱스를 나타내며, 리스트 형태로 입력합니다.
- h는 필터 강도를 나타내며, float 형태로 입력합니다.(default: 3)
- templateWindowSize는 template Patch의 pixel size를 나타내며, int 형태로 입력합니다. (default: 7)
- searchWindowSize는 weighted average를 계산할 때 사용하는 window의 pixel size를 나타내며, int 형태로 입력합니다. (default: 21)
- 다양한 dtype으로 입력된 밴드는, 해당 operation 처리 내에서 2~98%의 값으로 정규화(0-255)되어 처리됩니다.
- 노이즈 제거에 대한 자세한 정보는 https://docs.opencv.org/3.4/d1/d79/group__photo__denoise.html#ga4c6b0031f56ea3f98f768881279ffe93 를 참고하세요.
   
- nl_mean_denoising 예:
```yaml
processor_1:
  operations: [..., nl_mean_denoising, ...]
  ...
  nl_mean_denoising:
    bands: [1, 2, 3] # 노이즈 제거를 수행할 밴드
    h: 3 # 필터 강도
    templateWindowSize: 7 # template Patch의 pixel size
    searchWindowSize: 21 # weighted average를 계산할 때 사용하는 window의 pixel size
...
```

```yaml
processor_1:
  operations: [..., nl_mean_denoising, ...]
  ...
  nl_mean_denoising: # argument 전체에 default 값이 있으므로 빈 공백으로 두더라도 동작 가능
```

- ### apply_orbit
- apply_orbit은 Sentinel-1 영상의 궤도 정보를 메타데이터에 적용하는 operation입니다.
- orbit_type은 궤도 정보를 적용할 방법을 나타냅니다(default: 'SENTINEL_PRECISE')
  - 'SENTINEL_PRECISE', 'SENTINEL_RESTITUTED', 'DORIS_POR', 'DORIS_VOR', 'DELFT_PRECISE', 'PRARE_PRECISE', 'K5_PRECISE' 중 하나를 사용할 수 있습니다.
- poly_degree는 궤도 정보를 적용할 때 사용할 다항식의 차수를 나타냅니다(default: 3)
- continue_on_fail은 궤도 정보 적용 중 실패 시, 계속 진행할 지 여부를 나타냅니다(default: False)
- apply_orbit은 이전 operation에서 전달된 영상이 snap module인 경우에만 사용할 수 있습니다.
   

- apply_orbit 예:
```yaml
processor_1:
  operations: [..., apply_orbit, ...]
  ...
  apply_orbit:
    orbit_type: 'SENTINEL_PRECISE' # 궤도 정보를 적용할 방법
    poly_degree: 3 # 궤도 정보를 적용할 때 사용할 다항식의 차수
    continue_on_fail: False # 궤도 정보 적용 중 실패 시, 계속 진행할 지 여부
...
```

- ### calibrate
- calibrate는 Sentinel-1 영상의 데이터를 Backscatter 계수로 변환하는 operation입니다.
- polarizations는 변환할 밴드의 극성을 나타내며, 리스트 형태로 입력합니다.
  - 'VV', 'VH', 'HH', 'HV' 중 하나를 사용할 수 있습니다.
  - 공백으로 둘 경우, 영상이 가진 모든 극성에 대해 변환을 수행합니다.
- output_sigma는 변환된 데이터에 대한 sigma0 값을 출력할 지 여부를 나타냅니다(default: True)
- output_beta는 변환된 데이터에 대한 beta0 값을 출력할 지 여부를 나타냅니다(default: False)
- output_gamma는 변환된 데이터에 대한 gamma0 값을 출력할 지 여부를 나타냅니다(default: False)
- output_in_db는 변환된 데이터를 dB로 출력할 지 여부를 나타냅니다(default: False)
- output_in_complex는 변환된 데이터를 복소수로 출력할 지 여부를 나타냅니다(default: False)
- calibrate는 이전 operation에서 전달된 영상이 snap module인 경우에만 사용할 수 있습니다

- calibrate 예:
```yaml
processor_1:
  operations: [..., calibrate, ...]
  ...
  calibrate:
    polarizations: ['VV', 'VH'] # 변환할 밴드의 극성
    output_sigma: True # 변환된 데이터에 대한 sigma0 값을 출력할 지 여부
    output_beta: False # 변환된 데이터에 대한 beta0 값을 출력할 지 여부
    output_gamma: False # 변환된 데이터에 대한 gamma0 값을 출력할 지 여부
    output_in_db: False # 변환된 데이터를 dB로 출력할 지 여부
    output_in_complex: False # 변환된 데이터를 복소수로 출력할 지 여부
...
```
```yaml
processor_1:
  operations: [..., calibrate, ...]
  ...
  calibrate: # argument 전체에 default 값이 있으므로 빈 공백으로 두더라도 동작 가능
```

- ### terrain_correction
- terrain_correction은 Sentinel-1 영상의 데이터를 지형 보정하는 operation입니다.
- bands는 지형 보정을 수행할 밴드의 이름 혹은 인덱스를 나타내며, 리스트 형태로 입력합니다.
- dem_name은 지형 보정에 사용할 DEM 데이터의 이름을 나타내며, 문자열로 입력합니다. (default: 'SRTM_3SEC')
 - 'COPERNICUS_30', 'COPERNICUS_90', 'SRTM_3SEC', 'SRTM_1SEC_HGT', 'ACE30', 'GETASSE30' 중 하나를 사용할 수 있습니다.
- pixel_spacing_meter는 지형 보정을 수행할 때 사용할 pixel spacing을 meter 단위로 나타내며, float 형태로 입력합니다.(default: 0.0)
- pixel_spacing_degree는 지형 보정을 수행할 때 사용할 pixel spacing을 degree 단위로 나타내며, float 형태로 입력합니다.(default: 0.0)
- pixel_spacing_meter와 pixel_spacing_degree가 모두 0.0일 경우, 이전 operation에서 전달된 데이터의 pixel spacing을 사용합니다.
- dem_method은 지형 보정을 수행할 때 사용할 DEM 데이터의 interpolation 방법을 나타내며, 문자열로 입력합니다.(default: 'BILINEAR_INTERPOLATION')
  - 'NEAREST_NEIGHBOUR', 'BILINEAR_INTERPOLATION', 'CUBIC_CONVOLUTION', 'BISINC_5_POINT_INTERPOLATION', 'BISINC_11_POINT_INTERPOLATION', 'BISINC_21_POINT_INTERPOLATION', 'BICUBIC_INTERPOLATION' 중 하나를 사용할 수 있습니다.
- img_method은 지형 보정을 수행할 때 사용할 영상 데이터의 interpolation 방법을 나타내며, 문자열로 입력합니다.(default: 'BILINEAR_INTERPOLATION')
  - dem_method와 동일합니다.
- save_dem은 지형 보정을 수행할 때 사용한 DEM 데이터를 저장할 지 여부를 나타내며, bool 형태로 입력합니다.(default: False)
- epsg는 지형 보정을 수행할 때 사용할 좌표계의 epsg 코드를 나타내며, int 형태로 입력합니다.(default: 4326)
- terrain_correction은 이전 operation에서 전달된 영상이 snap module인 경우에만 사용할 수 있습니다.
   

- terrain_correction 예:
```yaml
processor_1:
  operations: [..., terrain_correction, ...]
  ...
  terrain_correction:
    bands: ['VV', 'VH'] # 지형 보정을 수행할 밴드
    dem_name: 'SRTM_3SEC' # 지형 보정에 사용할 DEM 데이터의 이름
    pixel_spacing_meter: 10.0 # 지형 보정을 수행할 때 사용할 pixel spacing(meter)
    pixel_spacing_degree: 0.0 # 지형 보정을 수행할 때 사용할 pixel spacing(degree)
    dem_method: 'BILINEAR_INTERPOLATION' # 지형 보정을 수행할 때 사용할 DEM 데이터의 interpolation 방법
    img_method: 'BILINEAR_INTERPOLATION' # 지형 보정을 수행할 때 사용할 영상 데이터의 interpolation 방법
    save_dem: False # 지형 보정을 수행할 때 사용한 DEM 데이터를 저장할 지 여부
    epsg: 4326 # 지형 보정을 수행할 때 사용할 좌표계의 epsg 코드
```
```yaml
processor_1:
  operations: [..., terrain_correction, ...]
  ...
  terrain_correction: # argument 전체에 default 값이 있으므로 빈 공백으로 두더라도 동작 가능
```

- ### speckle_filter
- speckle_filter는 Sentinel-1 영상의 speckle noise를 제거하는 operation입니다.
- bands는 speckle noise를 제거할 band의 이름 혹은 인덱스를 나타내며, 리스트 형태로 입력합니다.
- filter는 speckle noise를 제거할 때 사용할 필터를 나타내며, 문자열로 입력합니다. (default: 'LEE_SIGMA')
  - 'BOXCAR', 'MEDIAN', 'FROST', 'GAMMA_MAP', 'LEE_SPECKLE', 'LEE_REFINED', 'LEE_SIGMA', 'IDAN', 'MEAN_SPECKLE' 중 하나를 사용할 수 있습니다.
- dampling_factor는 speckle noise를 제거할 때 사용할 damping factor를 나타내며, int 형태로 입력합니다.(default: 2)
- filter_size는 speckle noise를 제거할 때 사용할 필터의 크기를 나타내며, 리스트 형태로 입력합니다.(default: [3, 3])
- number_looks는 speckle noise를 제거할 때 사용할 number of looks를 나타내며, int 형태로 입력합니다.(default: 1)
- window_size는 speckle noise를 제거할 때 사용할 window size를 나타내며, 문자열로 입력합니다.(default: '7x7')
  - '5x5', '7x7', '9x9', '11x11', '13x13', '15x15', '17x17' 중 하나를 사용할 수 있습니다.
- target_window_size는 speckle noise를 제거할 때 사용할 target window size를 나타내며, 문자열로 입력합니다.(default: '3x3')
  - '3x3', '5x5' 중 하나를 사용할 수 있습니다.
- sigma는 speckle noise를 제거할 때 사용할 sigma의 percentage를 나타내며, 문자열로 입력합니다.(default: '0.9')
  - '0.5', '0.6', '0.7', '0.8', '0.9' 중 하나를 사용할 수 있습니다.
- an_size는 speckle noise를 제거할 때 사용할 adaptive neighborhood size를 나타내며, int 형태로 입력합니다.(default: 50)
  - 1 - 200 사이의 값을 입력할 수 있습니다.
- speckle_filter는 이전 operation에서 전달된 영상이 snap module인 경우에만 사용할 수 있습니다.

- speckle_filter 예:
```yaml
processor_1:
  operations: [..., speckle_filter, ...]
  ...
  speckle_filter:
    bands: ['VV', 'VH'] # speckle noise를 제거할 밴드
    filter: 'LEE_SIGMA' # speckle noise를 제거할 때 사용할 필터
    dampling_factor: 2 # speckle noise를 제거할 때 사용할 damping factor
    filter_size: [3, 3] # speckle noise를 제거할 때 사용할 필터의 크기
    number_looks: 1 # speckle noise를 제거할 때 사용할 number of looks
    window_size: '7x7' # speckle noise를 제거할 때 사용할 window size
    target_window_size: '3x3' # speckle noise를 제거할 때 사용할 target window size
    sigma: '0.9' # speckle noise를 제거할 때 사용할 sigma의 percentage
    an_size: 50 # speckle noise를 제거할 때 사용할 adaptive neighborhood size
```
```yaml
processor_1:
  operations: [..., speckle_filter, ...]
  ...
  speckle_filter: # argument 전체에 default 값이 있으므로 빈 공백으로 두더라도 동작 가능
```

- ### thermal_noise_removal
- thermal_noise_removal은 Sentinel-1 영상의 thermal noise를 제거하는 operation입니다.
- polarizations는 thermal noise를 제거할 band의 극성을 나타내며, 리스트 형태로 입력합니다.
  - 'VV', 'VH', 'HH', 'HV' 중 하나를 사용할 수 있습니다.
- thermal_noise_removal은 이전 operation에서 전달된 영상이 snap module인 경우에만 사용할 수 있습니다.
   

- thermal_noise_removal 예:
```yaml
processor_1:
  operations: [..., thermal_noise_removal, ...]
  ...
  thermal_noise_removal:
    polarizations: ['VV', 'VH'] # thermal noise를 제거할 밴드의 극성
```
```yaml
processor_1:
  operations: [..., thermal_noise_removal, ...]
  ...
  thermal_noise_removal: # argument 전체에 default 값이 있으므로 빈 공백으로 두더라도 동작 가능
```

- ### topsar_deburst
- topsar_deburst는 Sentinel-1 slc 영상의 burst를 제거하는 operation입니다.
- polarizations는 burst를 제거할 band의 극성을 나타내며, 리스트 형태로 입력합니다.
  - 'VV', 'VH', 'HH', 'HV' 중 하나를 사용할 수 있습니다.
- topsar_deburst는 이전 operation에서 전달된 영상이 snap module인 경우에만 사용할 수 있습니다.
   

- topsar_deburst 예:
```yaml
processor_1:
  operations: [..., topsar_deburst, ...]
  ...
  topsar_deburst:
    polarizations: ['VV', 'VH'] # burst를 제거할 밴드의 극성
```
```yaml
processor_1:
  operations: [..., topsar_deburst, ...]
  ...
  topsar_deburst: # argument 전체에 default 값이 있으므로 빈 공백으로 두더라도 동작 가능
```
---
## References

source codes in atmos package are based on the following repositories:

* acolite, https://github.com/acolite/acolite

The Dark Spectrum Fitting (DSF) algorithm was presented in:
   

* Vanhellemont and Ruddick 2018, [Atmospheric correction of metre-scale optical satellite data for inland and coastal water applications](https://www.sciencedirect.com/science/article/pii/S0034425718303481)

* Vanhellemont 2019a, [Adaptation of the dark spectrum fitting atmospheric correction for aquatic applications of the Landsat and Sentinel-2 archives](https://doi.org/10.1016/j.rse.2019.03.010)

* Vanhellemont 2019b, [Daily metre-scale mapping of water turbidity using CubeSat imagery.](https://doi.org/10.1364/OE.27.0A1372)

New settings were suggested in:

* Vanhellemont 2020c, [Sensitivity analysis of the dark spectrum fitting atmospheric correction for metre- and decametre-scale satellite imagery using autonomous hyperspectral radiometry](https://doi.org/10.1364/OE.397456)

The adaptation to Sentinel-3/OLCI and SuperDove was presented in:

* Vanhellemont and Ruddick 2021, [Atmospheric correction of Sentinel-3/OLCI data for mapping of suspended particulate matter and chlorophyll-a concentration in Belgian turbid coastal waters](https://doi.org/10.1016/j.rse.2021.112284)

* Vanhellemont 2023, [Evaluation of eight band SuperDove imagery for aquatic applications](https://doi.org/10.1364/OE.483418)

First results using ACOLITE/DSF for PRISMA are presented in:

* Braga et al. 2022, [Assessment of PRISMA water reflectance using autonomous hyperspectral radiometry](http://dx.doi.org/10.1016/j.isprsjprs.2022.08.009)

The Thermal Atmospheric Correction Tool (TACT) is now integrated in ACOLITE and allows for processing of Landsat thermal band data to surface temperatures. TACT was presented in:

* Vanhellemont 2020a, [Automated water surface temperature retrieval from Landsat 8/TIRS](https://doi.org/10.1016/j.rse.2019.111518)

* Vanhellemont 2020b, [Combined land surface emissivity and temperature estimation from Landsat 8 OLI and TIRS](https://doi.org/10.1016/j.isprsjprs.2020.06.007)

TACT performance for Antarctic mountain sites and near shore waters was evaluated in:

* Vanhellemont et al. 2021a, [Towards physical habitat characterisation in the Antarctic Sør Rondane Mountains using satellite remote sensing](https://doi.org/10.1016/j.rsase.2021.100529)

* Vanhellemont et al. 2022, [Validation of Landsat 8 high resolution Sea Surface Temperature using surfers](https://doi.org/10.1016/j.ecss.2021.107650)
---
## 주의 사항
- __개발 환경에서는 정상 동작을 이미 확인하였지만, 환경 변화에 따른 코드 테스트를 아직 수행되지 않았습니다.__
- __YAML 작성을 위한 제약조건은 설정하였으나, 작성 편의를 위한 IDE가 제공되지 않고, 디버깅을 위한 Logger 기능이 아직 완벽하게 동작하지 않으므로, YAML 작성을 위해서는 test 코드를 활용한 디버깅 방법을 추천드립니다.__
- 향후 가능한 업데이트를 진행할 예정입니다. 감사합니다