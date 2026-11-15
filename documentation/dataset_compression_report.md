# NASA Dataset Compression Report

## Scope and safety

The original NASA files were read only and were not overwritten, deleted,
resampled, or modified. Compressed copies are stored under
[`datasets/github_compressed/`](../datasets/github_compressed/).

7-Zip, standalone `gzip`, and standalone `zip` executables were not installed
on the workstation. Python's standard-library gzip and ZIP implementations
were used at maximum compression level instead. The LOLA source is already an
internally compressed NPZ archive; an outer ZIP was tested to measure whether
it produced a useful reduction.

GitHub's normal individual-file limit is 100 MiB (104,857,600 bytes). A file
is marked `READY` only when its compressed copy is strictly below that limit.

## Results

| Dataset | Original size | Method | Compressed copy | Compressed size | Reduction | SHA-256 verification | GitHub status |
|---|---:|---|---:|---:|---:|---|---|
| `global_cumul_avg_cyl_80s70s_002.tab` | 156,211,313 bytes (148.97 MiB) | GZIP maximum, level 9 | `global_cumul_avg_cyl_80s70s_002.tab.gz` | 40,722,341 bytes (38.83 MiB) | 73.9312% | PASS | **READY** |
| `global_cumul_avg_cyl_80s70s_002.tab` | 156,211,313 bytes (148.97 MiB) | ZIP maximum, deflate level 9 | `global_cumul_avg_cyl_80s70s_002.tab.zip` | 40,722,455 bytes (38.83 MiB) | 73.9312% | PASS | **READY** |
| `ldem_16_processed.npz` | 106,424,701 bytes (101.49 MiB) | ZIP maximum, outer archive, deflate level 9 | `ldem_16_processed.npz.zip` | 106,282,838 bytes (101.36 MiB) | 0.1333% | PASS | **NOT READY** |

## SHA-256 verification

Each archive was extracted into a temporary directory. The extracted file
size and SHA-256 were compared with the original:

### Diviner

- Original SHA-256:
  `c6c9b3a84e1e9972237b07fd8dd1c0f44899ab8ffe9a403a7528ef7cd38b1cda`
- GZIP extracted SHA-256:
  `c6c9b3a84e1e9972237b07fd8dd1c0f44899ab8ffe9a403a7528ef7cd38b1cda`
- ZIP extracted SHA-256:
  `c6c9b3a84e1e9972237b07fd8dd1c0f44899ab8ffe9a403a7528ef7cd38b1cda`
- Result: **both copies match the original exactly**.

### LOLA

- Original SHA-256:
  `e0682e4c5168b028bf17999c8ab59eec8df887f315145c8f3e5c8a3ae9e50562`
- Outer ZIP extracted SHA-256:
  `e0682e4c5168b028bf17999c8ab59eec8df887f315145c8f3e5c8a3ae9e50562`
- Result: **the extracted copy matches the original exactly**.

## Interpretation

- **Best Diviner method:** GZIP at maximum compression, narrowly smaller than
  the maximum ZIP copy.
- **Best LOLA method:** The tested outer ZIP was the only requested available
  method, but it reduced the already-compressed NPZ by only 0.1333%.
- **GitHub compatibility:** Both Diviner compressed copies are below 100 MiB.
  The LOLA outer ZIP remains above 100 MiB and is therefore **not ready** for
  normal GitHub upload.
- No information was removed, and no dataset resolution or records changed.

The compressed copies are test artifacts only. No Git commit or GitHub upload
was performed.
