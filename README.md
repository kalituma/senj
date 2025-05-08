# Senj
[![ko](https://img.shields.io/badge/lang-ko-blue.svg)](https://github.com/kalituma/senj/blob/main/README.ko.md)

- YAML-based Snap and GDAL preprocessing library
- The atmospheric correction processor included in Senj utilizes source code from acolite (https://github.com/acolite/acolite).
- being developed by kalituma and Curious_Coldbrew at AIRS lab., PKNU

---

## Required Packages
- gdal, cv2, jsonpath_ng, pyyaml, scipy, matplotlib, lxml, 
requests, pyresample, pyhdf, netCDF4, tqdm, scikit-image,
cerberus, networkx

---

## Required Programs
- snap(esa-snappy)

---
## Running the Preprocessing Library

- The preprocessing module performs preprocessing by reading a YAML Configuration file written by the user.
- The python script for running the preprocessing module is LIBRARY/senj/execute/run_config.py.
- The python script options are --config_path, --log_dir, and --log_level.
- --config_path represents the path to the YAML Configuration file written by the user.
- --log_dir represents the directory path where log files will be stored.
- --log_level represents the log level for output (DEBUG, INFO, WARNING, ERROR, CRITICAL).

```bash
python path/to/run_config.py --config_path 'path/to/config.yaml' --log_dir 'path/to/log' --log_level 'DEBUG'
```
---

## How to Write YAML

- YAML uses indentation to hierarchically express preprocessing procedures.
- The conceptual elements that make up YAML for preprocessing are processor and operation.
- A processor is a unit of preprocessing that includes operations and must include items such as input, operations, etc.
- The name of the processor can be defined according to the user's purpose.
- The previously defined processor name is used in the input item of subsequent processors to connect between processors.
- An operation is a unit that processes data within a processor, with predefined names such as 'read', 'write', etc.

```yaml
processor_1: # processor name can be modified
  input:
    ... 
  operations: [read, resample, ...] # operation names cannot be modified
  read:   # write operations included in operations that require arguments
    ...
  resample:
    ...

processor_2:
  input:
    path: '{{processor_1}}' # means using output data from processor_1
  operations:
    [clip, select, ...]
  clip:
    ...
  select:
    ...
```

- ### Input

  - The input item defines the input data for the processor.
  - The input item can include items such as path, pattern, sort, etc.
  - path represents the path of the input data and can use file paths, directory paths, or processor links.
  

    
```yaml
processor_1:
  input:
    path: 'path/to/file1' # using a single file path
```
- Multiple file paths can be used in list form.
```yaml
processor_1:
    input:
      path: ['path/to/file1', 'path/to/file2', ...] # using multiple file paths
```

- For directory paths, pattern and sort items can be used.
- pattern is used when you want to use only files with a specific pattern within the directory (using glob pattern).
- sort is used to sort the files loaded from the set directory when they have a pattern.
- In sort's func, you can specify a sorting function in the format ___'!{function name}'___.
- You can use functions defined in LIBRARY/senj/core.lambda_funcs.sort_lambda.py or define your own function.
```yaml
processor_1:
  input:
    path: 'path/to/dir' # using a directory path
    pattern: '*.tif' # using only files with a specific pattern (e.g., tif extension) within the directory
    sort:
      func: '!{sort_by_something}' # using a file sorting method
```

- When defining a function to use in sort's func, register it with the lambda object.

```python
@LAMBDA.reg(name='sort_by_something') # register the function with lambda, 'sort_by_something' used here is used in sort's func
def sort_by_last_number(file_name: str) -> int:
    return int(Path(file_name).stem.split('_')[-1]) # sort by the last number in files composed in the form xxx_xxx_1.tif
```

- processor link is used when using output data from another processor.
- processor link is used in the form ___'{{processor_name}}'___.
```yaml
processor_1:
    ...
processor_2:
  input:
    path: '{{processor_1}}' # using a single link
```

- When using multiple processor links, use them in list form.
```yaml
processor_1:
    ...
processor_2:
    ...
processor_3:
  input:
    path: ['{{processor_1}}', '{{processor_2}}'] # using multiple links
```

---


## Operations 

|       Operation Name       |          Available Product type           |                                                                                arguments                                                                                 |   module   |                    description                    |
|:--------------------------:|:-----------------------------------------:|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|:----------:|:-------------------------------------------------:|
|            read            |                    All                    |                                             ___module(str)___, bands(list[int, str]), bword(str), bname_word_included(bool)                                              | gdal, snap |                                                   |          
|           write            |                    All                    |                             ___out_path(str)___, ___out_dir(str)___, out_stem(str), out_ext(str), bands(list[int, str]), prefix(str), suffix(str)                             | gdal, snap |        specify either out_path or out_dir         |
|          convert           |                    All                    |                                                                           ___to_module(str)___                                                                           | gdal, snap |                                                   |
|          resample          |                    All                    |                                                           epsg(int), pixel_size(float), resampling_method(str)                                                           | gdal, snap |           either epsg or pixel_size is required           |
|            clip            |                    All                    |                                                               ___bounds(list[float])___, bounds_espg(int)                                                                | gdal, snap |                                                   |
|           select           |                    All                    |                                                              bands(list[int, str]), band_labels(list[str])                                                               | gdal, snap |          either band or band_labels is required           |
|           mosaic           |                    All                    |                                                             ___master_module(str)___, bands(list[str, int])                                                              | gdal, snap |              needs improvement for snap module               |
|           stack            |                    All                    |                                                                   band_list(list[list[int,str], None])                                                                   | gdal, snap |                                                   |
|         atmos_corr         | Sentinel-2, WorldView/GeoEye, PlanetScope | ___bands___[List[str, int]], ___band_slots___(List[str]), write_map(bool), map_dir(str), map_stem(str), det_bnames(List[str]), det_bword_include(bool), det_pattern(str) | gdal, snap | choose between det_bnames, det_bword_include, or det_pattern |
| backscattering_coefficient |                    All                    |                                                              bands(list[int, str]), drop_other_bands(bool)                                                               | gdal, snap |                                                   |
|   cached_speckle_filter    |                    All                    |                                                              bands(list[int, str]), drop_other_bands(bool)                                                               | gdal, snap |                                                   |
|         normalize          |                    All                    |                                                       method([str]), min(float), max(float), bands(list[int,str])                                                        | gdal, snap |        method can be either percentile or minmax         |
|          rev_ref           |                    All                    |                                                                                                                                                                          | gdal, snap |               converts calculated index reflectance back to dn values               |
|     nl_mean_denoising      |                    All                    |                                              bands(List[int,str]), h(float), templateWindowSize(int), searchWindowSize(int)                                              | gdal, snap |                                                   |
|        apply_orbit         |                Sentinel-1                 |                                                        orbit_type(str), poly_degree(int), continue_on_fail(bool)                                                         |    snap    |
|         calibrate          |                Sentinel-1                 |                     polarizations(List[str]), output_sigma(bool), output_beta(bool), output_gamma(bool), output_in_db(bool), output_in_complex(bool)                     |    snap    |                                                   |
|     terrain_correction     |                Sentinel-1                 |        bands(List[str, int]), dem_name(str), pixel_spacing_meter(float), pixel_spacing_degree(float), dem_method(str), img_method(str), save_dem(bool), epsg(int)        |    snap    |                                                   |
|       speckle_filter       |                Sentinel-1                 | bands(List[str, int]), filter(str), dampling_factor(int), filter_size(list[int]), number_looks(int), window_size(str), target_window_size(str), sigma(str), an_size(int) |    snap    |                                                   |
|   thermal_noise_removal    |                Sentinel-1                 |                                                                         polarizations(List[str])                                                                         |    snap    |                                                   |
|       topsar_deburst       |                Sentinel-1                 |                                                                         polarizations(List[str])                                                                         |    snap    |                                                   |

* ___Emphasized and italicized items___ in arguments indicate required arguments

- ### Read
- read is an operation that reads input data and can be included first in the operations list that makes up the processor.
- In read, module represents the module used when handling data and can use either gdal or snap.
- bands represents the name or index of the band to read and is input in list form.
- bword represents the pattern (glob pattern) of words included in the band name, and when bname_word_included is input as True, only bands with bword included in the band name are read.
- Either bands or bword can be chosen to use, and bands always takes precedence over bword.
- The default value of bands is all bands (None), the default value of bword is *, and the default value of bname_word_included is False.
   

- Read example:
```yaml
processor_1:
  operations: [read, ...]
  read:
    module: 'gdal' # either gdal or snap
    bands: [1, 2, 3] # bands to read    
...
```
```yaml
processor_1:
  operations: [read, ...]
  read:
    module: 'gdal' # either gdal or snap
    bands: ['B01', 'B02', 'B03'] # bands to read
...
```
```yaml
processor_1:
  operations: [read, ...]
  read:
    module: 'gdal' # either gdal or snap
    bword: '*B01*' # only read bands with B01 in the name
    bname_word_included: True # only read bands with B01 in the name
...
```

- ### Write
- write is an operation that saves preprocessing results to disk and can be included last in the operations list that makes up the processor.
- out_path represents the absolute path of the file to save.
- out_dir represents the directory path to save, and out_stem represents the stem of the file name to save.
- Either out_path or out_dir can be used.
- out_ext, out_stem, prefix, and suffix are variables used when using out_dir.
- out_ext represents the extension of the file to save, and bands represents the name or index of the band to save.
- prefix represents the string to attach to the front of the file name, and suffix represents the string to attach to the back of the file name.
- The default value of out_stem is 'out', and the default value of out_ext varies depending on the module of the previously passed data.
  - If not specified, gdal is set to __tif__ and snap is set to __dim__, and if specified, gdal can be set to __tif__ and snap can be set to __dim,tif__.)
- The default value of bands is all bands (None), and the default values of prefix and suffix are ''.
- For input dir, stem, ext, prefix, suffix, and directory input, the final file name is generated by combining with the preprocessing iteration count.
- Example ) out_dir='path/to/dir', out_stem='out', out_ext='tif', prefix='pre', suffix='suf', count=1 -> 'path/to/dir/pre_out_suf.1.tif'
   

- Write example:
```yaml
processor_1:
  operations: [..., write]
  ...
  write:    
    out_path: 'path/to/file.extension' # absolute path of the file to save, not used when using out_dir
    out_dir: 'path/to/dir' # directory path to save, not used when using out_path
    out_stem: 'out' # stem of the file name to save, only used when using out_dir
    out_ext: 'tif' # extension of the file to save, only used when using out_dir
    prefix: 'pre' # string to attach to the front of the file name, only used when using out_dir
    suffix: 'suf' # string to attach to the back of the file name, only used when using out_dir
    bands: [1, 2, 3, ...] # band indices to save
```
or
```yaml
processor_1:
  operations: [..., write]
  ...
  write:    
    out_path: 'path/to/file.extension' # absolute path of the file to save    
    bands: ['band_name_1', 'band_name_2', ...] # band names to save
    
```


- ### Convert
- convert is an operation that converts data to another format and changes the module of the previous operation to another module.
  - Example) gdal -> snap, snap -> gdal
- In convert, to_module represents the module to convert to and can use either gdal or snap.
   

- convert example:
```yaml
processor_1:
  operations: [read, convert, ...]
  read:
    module: 'gdal' # either gdal or snap
    bands: [1, 2, 3] # bands to read
  convert:
    to_module: 'snap' # module to convert to, data passed to subsequent operations will be snap module objects
...
``` 

- ### Resample
- resample is an operation that converts data to another resolution or coordinate system.
- In resample, epsg represents the epsg code of the coordinate system to convert to, and pixel_size represents the resolution to convert to.
- resampling_method represents the resampling method to use when converting and can vary depending on the module type of the data passed from the previous operation.
  - For gdal, resampling_method can use one of __'nearest', 'bilinear', 'bicubic', 'cubicspline', 'lanczos'__.
  - For snap, resampling_method can use one of __'nearest', 'bilinear', 'bicubic'__.
- Either epsg or pixel_size is required.
- epsg codes can be checked at https://epsg.io/.
   

- Resample example:
```yaml
processor_1:
  operations: [..., resample, ...]
  ...
  resample:
    epsg: 4326 # epsg code of the coordinate system to convert to
    pixel_size: 0.01 # resolution to convert to
    resampling_method: 'nearest' # resampling method to use when converting
...
```
- ### Subset
- clip is an operation that cuts data to a specific area.
- In clip, bounds represents the coordinates of the area to cut, and bounds_epsg represents the coordinate system of bounds.
- bounds is input in the form [min_x, max_y, max_x, min_y], and bounds_epsg represents the epsg code of the coordinate system.
- The default value of bounds_epsg is 4326.
   

- Subset example:
```yaml
processor_1:
  operations: [..., clip, ...]
  ...
  clip:
    bounds: [126.5, 38.5, 127.0, 38.0] # coordinates of the area to cut
    bounds_epsg: 4326 # epsg code of the coordinate system
...
```

- ### Select
- select is an operation that selects specific bands of data, changes the order of specific bands, or changes band names.
- bands represents the name or index of the band to select and is input in list form.
- band_labels represents the name of the band to change and is input in list form.
- Either bands or band_labels is required.
- When using band_labels, you must input the same number of band_labels as bands.
   

- Select example:
```yaml
processor_1:
  operations: [..., select, ...]
  ...
  select:
    bands: ['B2', 'B3', 'B4'] # bands to select
    band_labels: ['Blue', 'Green', 'Red'] # names to change the bands to
...
```

- ### Mosaic
- mosaic is an operation that combines multiple images into one based on x,y axes, and can combine the results of multiple processors into a list to make one processor result.
- In mosaic, master_module is a required argument that represents the module to perform the mosaic and can use gdal.
  - For snap, improvement is still needed and will be supported in the future.
- bands represents the name or index of the band to combine and is input in list form.
   

- Mosaic example:
```yaml
processor_1:
  ...
processor_2:
  ...
processor_3:
  input:
    path: ['{{processor_1}}', '{{processor_2}}'] # using results from processor_1, processor_2
  operations: [mosaic, ...]
  ...
  mosaic:
    master_module: 'gdal' # module to perform the mosaic
    bands: ['B2', 'B3', 'B4'] # bands to combine
...
```

- ### Stack
- stack is an operation that combines multiple images into one based on z-axis, and can combine the results of multiple processors into a list to make one processor result.
- In stack, band_list represents the name or index of the band to combine and is input in list form.
- If the band to combine is all bands of a specific image, input None.
- The default value of band_list is None.
- master_module represents the module to perform the stack and can use gdal or snap.
- meta_from represents the name of the processor link that can provide metadata to bring to the stack result data, and uses one of the processor links input in input.
- geo_err represents the allowable resolution error when checking if each band matches geographically (bounds, pixel_size) when performing the stack.
  - The default value of geo_err is 0.0001.
  

- Stack example:

```yaml
processor_1:
  ...
processor_2:
  ...
processor_3:
  ...

processor_4:
  input:
    path: ['{{processor_1}}', '{{processor_2}}', '{{processor_2}}'] # using results from processor_1, processor_2
  operations: [stack, ...]
    ...
  stack:
    master_module: 'gdal' # module to perform the stack
    band_list: [['Red', 'Green', 'Blue'], None, [1, 2, 3]] # bands to combine
    meta_from: '{{processor_1}}' # processor link to provide metadata to bring to the stack result data
    geo_err: 0.0001 # geographical error      
```

- ### atmos_corr
- atmos_corr is an operation that performs atmospheric correction on optical products.
- Currently supports Sentinel-2, WorldView/GeoEye, and PlanetScope.
- bands represents the name or index of the band to perform atmospheric correction on and is input in list form.
- band_slots is used to define the physical band slot of the band to perform atmospheric correction on and is input in list form.
  - For Sentinel-2, band_slots can use one of ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12'].
  - For WorldView, band_slots can use one of ['coastal', 'blue', 'green', 'yellow', 'red', 'rededge', 'nir1', 'nir2', 'pan'].
  - For GeoEye, band_slots can use one of ['pan', 'blue', 'green', 'red', 'nir'].
  - For PlanetScope, band_slots can use one of ['blue', 'green', 'red', 'nir'].
- write_map represents whether to save the atmospheric correction result as an image, and the default is False.
- map_dir represents the directory path to save the image when saving, and map_stem represents the file stem of the image to save.
- det_bnames represents the band name that stores information related to the image detector number and is input in list form (only for Sentinel-2 images).
  - For Sentinel-2 images, solar zenith angle, solar azimuth angle, view zenith angle, view azimuth angle, etc. vary according to the image detector number, and this argument is used as a means to obtain sensor-related parameters using this.
- det_bword_include is used when you want to query bands with detector number information using word patterns, and is set to True or False.
- det_pattern represents the pattern (glob pattern) used when querying bands with detector number information and is input as a string.
- Either det_bnames or det_bword_include, det_pattern can be used, and det_bnames takes precedence.

   
- atmos_corr example:
```yaml
# for sentinel-2,
processor_1: 
  operations: [..., atmos_corr, ...]
  ...
  atmos_corr:
    bands: [2, 3, 4] # bands to perform atmospheric correction on
    band_slots: ['B2', 'B3', 'B4'] # physical band slots of the bands to perform atmospheric correction on
    write_map: True # whether to save the atmospheric correction result as an image
    map_dir: 'path/to/dir' # directory path to save the image
    map_stem: 'sentinel2_corrected' # file stem of the image    
    det_bword_include: True # query bands with detector number information using word patterns
    det_pattern: 'B_detector*' # pattern used when querying bands with detector number information
```

```yaml
# for PlanetScope,
processor_1: 
  operations: [..., atmos_corr, ...]
  ...
  atmos_corr:
    bands: ['band_1', 'band_2', 'band_3', 'band_4'] # bands to perform atmospheric correction on
    band_slots: ['blue', 'green', 'red', 'nir'] # physical band slots of the bands to perform atmospheric correction on
    write_map: True # whether to save the atmospheric correction result as an image
    map_dir: 'path/to/dir' # directory path to save the image
    map_stem: 'planet_corrected' # file stem of the image
```
- ### backscattering_coefficient
- backscattering_coefficient is an operation that converts Sentinel-1 image data to Backscatter coefficients.
- bands represents the name or index of the band to convert and is input in list form.
- If bands is not input, conversion is performed on all bands.
- drop_other_bands represents whether to remove other bands except the converted data, and the default is False.
- backscattering_coefficient loads the band for conversion into memory to perform the conversion, so it can be used with snap and gdal images.

```yaml
processor_1:
  operations: [..., backscattering_coefficient, ...]
  ...
  backscattering_coefficient:
    bands: ['band_1', 'band_2', ...] # bands to convert
    drop_other_bands: False # whether to remove other bands except the converted data
...
```

- backscattering_coefficient example:

```yaml
processor_1:
  operations: [..., backscattering_coefficient, ...]
  ...
  backscattering_coefficient:    
    bands: [1, 2, 3] # convert bands 1,2,3
    drop_other_bands: true # whether to remove other bands except the converted data
...
```

- ### cached_speckle_filter
- cached_speckle_filter is an operation that loads the band to convert into memory to remove speckle noise.
- bands represents the name or index of the band to remove speckle noise from and is input in list form.
- If bands is not input, speckle noise removal is performed on all bands.
- drop_other_bands represents whether to remove other bands except the speckle noise removed data, and the default is False.
- cached_speckle_filter can be used with snap and gdal images.

```yaml
processor_1:
  operations: [..., cached_speckle_filter, ...]
  ...
  cached_speckle_filter:
    bands: ['band_1', 'band_2', ...] # bands to remove speckle noise from
    drop_other_bands: False # whether to remove other bands except the speckle noise removed data
...
```

- cached_speckle_filter example:

```yaml
processor_1:
  operations: [..., cached_speckle_filter, ...]
  ...
  cached_speckle_filter:    
    bands: [1, 2, 3] # remove speckle noise from bands 1,2,3
    drop_other_bands: true # whether to remove other bands except the speckle noise removed data
...
```

- ### normalize
- normalize is an operation that loads the band to convert into memory to normalize the data.
- method represents the normalization method and can use either percentile or minmax.
- min represents the minimum value to normalize (percentile in case of percentile), and max represents the maximum value to normalize (percentile in case of percentile).
- bands represents the name or index of the band to normalize and is input in list form.
- If bands is not input, normalization is performed on all bands.
- normalize can be used with snap and gdal images.

```yaml
processor_1:
  operations: [..., normalize, ...]
  ...
  normalize:
    method: 'percentile' # normalization method
    min: 2 # minimum value to normalize (percentile in case of percentile)
    max: 98 # maximum value to normalize (percentile in case of percentile)
    bands: ['band_1', 'band_2', ...] # bands to normalize
...
```

- normalize example:

```yaml
processor_1:
  operations: [..., normalize, ...]
  ...
  normalize:    
    method: 'minmax' # normalization method
    min: 0 # minimum value to normalize
    max: 255 # maximum value to normalize
    bands: [1, 2, 3] # normalize bands 1,2,3
...
```

- ### rev_ref
- rev_ref is an operation that converts the calculated index reflectance of Sentinel-2 back to dn values after atmospheric correction is completed.
- rev_ref operates by loading the band to convert into memory, so it can be used with snap and gdal images.

```yaml
processor_1:
  operations: [..., rev_ref, ...]
  ... # rev_ref does not require any arguments
```

- ### nl_mean_denoising
- nl_mean_denoising is an operation that removes noise from images using opencv's fastNlMeansDenoising function.
- bands represents the name or index of the band to perform noise removal on and is input in list form.
- h represents the filter strength and is input in float form (default: 3).
- templateWindowSize represents the pixel size of the template Patch and is input in int form (default: 7).
- searchWindowSize represents the pixel size of the window used when calculating the weighted average and is input in int form (default: 21).
- Bands input in various dtypes are normalized (0-255) to 2~98% values within this operation processing.
- For more information about noise removal, see https://docs.opencv.org/3.4/d1/d79/group__photo__denoise.html#ga4c6b0031f56ea3f98f768881279ffe93.

```yaml
processor_1:
  opertions: [..., nl_mean_denoising, ...]
```
- nl_mean_denoising example:
```yaml
processor_1:
  operations: [..., nl_mean_denoising, ...]
  ...
  nl_mean_denoising:
    bands: [1, 2, 3] # bands to perform noise removal on
    h: 3 # filter strength
    templateWindowSize: 7 # pixel size of the template Patch
    searchWindowSize: 21 # pixel size of the window used when calculating the weighted average
...
```

```yaml
processor_1:
  operations: [..., nl_mean_denoising, ...]
  ...
  nl_mean_denoising: # can operate even with empty space as all arguments have default values
```

- ### apply_orbit
- apply_orbit is an operation that applies orbit information to the metadata of Sentinel-1 images.
- orbit_type represents the method to apply orbit information (default: 'SENTINEL_PRECISE')
  - Can use one of 'SENTINEL_PRECISE', 'SENTINEL_RESTITUTED', 'DORIS_POR', 'DORIS_VOR', 'DELFT_PRECISE', 'PRARE_PRECISE', 'K5_PRECISE'.
- poly_degree represents the degree of the polynomial to use when applying orbit information (default: 3).
- continue_on_fail represents whether to continue when orbit information application fails (default: False).
- apply_orbit can only be used when the image passed from the previous operation is a snap module.
   

- apply_orbit example:
```yaml
processor_1:
  operations: [..., apply_orbit, ...]
  ...
  apply_orbit:
    orbit_type: 'SENTINEL_PRECISE' # method to apply orbit information
    poly_degree: 3 # degree of the polynomial to use when applying orbit information
    continue_on_fail: False # whether to continue when orbit information application fails
...
```

- ### calibrate
- calibrate is an operation that converts Sentinel-1 image data to Backscatter coefficients.
- polarizations represents the polarity of the band to convert and is input in list form.
  - Can use one of 'VV', 'VH', 'HH', 'HV'.
  - If left blank, conversion is performed on all polarities the image has.
- output_sigma represents whether to output sigma0 values for the converted data (default: True).
- output_beta represents whether to output beta0 values for the converted data (default: False).
- output_gamma represents whether to output gamma0 values for the converted data (default: False).
- output_in_db represents whether to output the converted data in dB (default: False).
- output_in_complex represents whether to output the converted data in complex numbers (default: False).
- calibrate can only be used when the image passed from the previous operation is a snap module.

- calibrate example:
```yaml
processor_1:
  operations: [..., calibrate, ...]
  ...
  calibrate:
    polarizations: ['VV', 'VH'] # polarity of the band to convert
    output_sigma: True # whether to output sigma0 values for the converted data
    output_beta: False # whether to output beta0 values for the converted data
    output_gamma: False # whether to output gamma0 values for the converted data
    output_in_db: False # whether to output the converted data in dB
    output_in_complex: False # whether to output the converted data in complex numbers
...
```
```yaml
processor_1:
  operations: [..., calibrate, ...]
  ...
  calibrate: # can operate even with empty space as all arguments have default values
```

- ### terrain_correction
- terrain_correction is an operation that performs terrain correction on Sentinel-1 image data.
- bands represents the name or index of the band to perform terrain correction on and is input in list form.
- dem_name represents the name of the DEM data to use for terrain correction and is input as a string (default: 'SRTM_3SEC').
 - Can use one of 'COPERNICUS_30', 'COPERNICUS_90', 'SRTM_3SEC', 'SRTM_1SEC_HGT', 'ACE30', 'GETASSE30'.
- pixel_spacing_meter represents the pixel spacing to use when performing terrain correction in meters and is input in float form (default: 0.0).
- pixel_spacing_degree represents the pixel spacing to use when performing terrain correction in degrees and is input in float form (default: 0.0).
- If both pixel_spacing_meter and pixel_spacing_degree are 0.0, the pixel spacing of the data passed from the previous operation is used.
- dem_method represents the interpolation method of the DEM data to use when performing terrain correction and is input as a string (default: 'BILINEAR_INTERPOLATION').
  - Can use one of 'NEAREST_NEIGHBOUR', 'BILINEAR_INTERPOLATION', 'CUBIC_CONVOLUTION', 'BISINC_5_POINT_INTERPOLATION', 'BISINC_11_POINT_INTERPOLATION', 'BISINC_21_POINT_INTERPOLATION', 'BICUBIC_INTERPOLATION'.
- img_method represents the interpolation method of the image data to use when performing terrain correction and is input as a string (default: 'BILINEAR_INTERPOLATION').
  - Same as dem_method.
- save_dem represents whether to save the DEM data used when performing terrain correction and is input in bool form (default: False).
- epsg represents the epsg code of the coordinate system to use when performing terrain correction and is input in int form (default: 4326).
- terrain_correction can only be used when the image passed from the previous operation is a snap module.
   

- terrain_correction example:
```yaml
processor_1:
  operations: [..., terrain_correction, ...]
  ...
  terrain_correction:
    bands: ['VV', 'VH'] # bands to perform terrain correction on
    dem_name: 'SRTM_3SEC' # name of the DEM data to use for terrain correction
    pixel_spacing_meter: 10.0 # pixel spacing to use when performing terrain correction (meters)
    pixel_spacing_degree: 0.0 # pixel spacing to use when performing terrain correction (degrees)
    dem_method: 'BILINEAR_INTERPOLATION' # interpolation method of the DEM data to use when performing terrain correction
    img_method: 'BILINEAR_INTERPOLATION' # interpolation method of the image data to use when performing terrain correction
    save_dem: False # whether to save the DEM data used when performing terrain correction
    epsg: 4326 # epsg code of the coordinate system to use when performing terrain correction
```
```yaml
processor_1:
  operations: [..., terrain_correction, ...]
  ...
  terrain_correction: # can operate even with empty space as all arguments have default values
```

- ### speckle_filter
- speckle_filter is an operation that removes speckle noise from Sentinel-1 images.
- bands represents the name or index of the band to remove speckle noise from and is input in list form.
- filter represents the filter to use when removing speckle noise and is input as a string (default: 'LEE_SIGMA').
  - Can use one of 'BOXCAR', 'MEDIAN', 'FROST', 'GAMMA_MAP', 'LEE_SPECKLE', 'LEE_REFINED', 'LEE_SIGMA', 'IDAN', 'MEAN_SPECKLE'.
- dampling_factor represents the damping factor to use when removing speckle noise and is input in int form (default: 2).
- filter_size represents the size of the filter to use when removing speckle noise and is input in list form (default: [3, 3]).
- number_looks represents the number of looks to use when removing speckle noise and is input in int form (default: 1).
- window_size represents the window size to use when removing speckle noise and is input as a string (default: '7x7').
  - Can use one of '5x5', '7x7', '9x9', '11x11', '13x13', '15x15', '17x17'.
- target_window_size represents the target window size to use when removing speckle noise and is input as a string (default: '3x3').
  - Can use one of '3x3', '5x5'.
- sigma represents the percentage of sigma to use when removing speckle noise and is input as a string (default: '0.9').
  - Can use one of '0.5', '0.6', '0.7', '0.8', '0.9'.
- an_size represents the adaptive neighborhood size to use when removing speckle noise and is input in int form (default: 50).
  - Can input a value between 1 and 200.
- speckle_filter can only be used when the image passed from the previous operation is a snap module.

- speckle_filter example:
```yaml
processor_1:
  operations: [..., speckle_filter, ...]
  ...
  speckle_filter:
    bands: ['VV', 'VH'] # bands to remove speckle noise from
    filter: 'LEE_SIGMA' # filter to use when removing speckle noise
    dampling_factor: 2 # damping factor to use when removing speckle noise
    filter_size: [3, 3] # size of the filter to use when removing speckle noise
    number_looks: 1 # number of looks to use when removing speckle noise
    window_size: '7x7' # window size to use when removing speckle noise
    target_window_size: '3x3' # target window size to use when removing speckle noise
    sigma: '0.9' # percentage of sigma to use when removing speckle noise
    an_size: 50 # adaptive neighborhood size to use when removing speckle noise
```
```yaml
processor_1:
  operations: [..., speckle_filter, ...]
  ...
  speckle_filter: # can operate even with empty space as all arguments have default values
```

- ### thermal_noise_removal
- thermal_noise_removal is an operation that removes thermal noise from Sentinel-1 images.
- polarizations represents the polarity of the band to remove thermal noise from and is input in list form.
  - Can use one of 'VV', 'VH', 'HH', 'HV'.
- thermal_noise_removal can only be used when the image passed from the previous operation is a snap module.
   

- thermal_noise_removal example:
```yaml
processor_1:
  operations: [..., thermal_noise_removal, ...]
  ...
  thermal_noise_removal:
    polarizations: ['VV', 'VH'] # polarity of the band to remove thermal noise from
```
```yaml
processor_1:
  operations: [..., thermal_noise_removal, ...]
  ...
  thermal_noise_removal: # can operate even with empty space as all arguments have default values
```

- ### topsar_deburst
- topsar_deburst is an operation that removes bursts from Sentinel-1 slc images.
- polarizations represents the polarity of the band to remove bursts from and is input in list form.
  - Can use one of 'VV', 'VH', 'HH', 'HV'.
- topsar_deburst can only be used when the image passed from the previous operation is a snap module.
   

- topsar_deburst example:
```yaml
processor_1:
  operations: [..., topsar_deburst, ...]
  ...
  topsar_deburst:
    polarizations: ['VV', 'VH'] # polarity of the band to remove bursts from
```
```yaml
processor_1:
  operations: [..., topsar_deburst, ...]
  ...
  topsar_deburst: # can operate even with empty space as all arguments have default values
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
## Notes
- __Normal operation has been confirmed in the development environment, but code testing according to environmental changes has not yet been performed.__
- __Constraints for YAML writing have been set, but since an IDE for writing convenience is not provided and the Logger function for debugging does not yet work perfectly, it is recommended to use test code for debugging when writing YAML.__
- Future updates are planned. Thank you.