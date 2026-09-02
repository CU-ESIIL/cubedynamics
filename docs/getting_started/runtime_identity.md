# Runtime identity in notebooks

## Which CubeDynamics code is this kernel actually running?

A package version identifies a release line. It does not prove which files an
already-running notebook imported. During release hardening, `main` can retain
the same semantic version as the latest public candidate while containing later
commits.

```python
import cubedynamics as cd

identity = cd.version_info()
print(identity)
identity.as_dict()
```

The record distinguishes:

- `published or built distribution`: an installed wheel or sdist without VCS
  checkout metadata;
- `VCS installation`: an installation whose `direct_url.json` records a Git
  commit; and
- `development checkout`: code imported from inside a Git working tree.

It also reports the imported package path, installed distribution location,
source URL when available, editable-install status, and Git SHA when it can be
read locally. The helper performs no network request.

## Kernel rule

After installing or changing CubeDynamics, restart the kernel before importing
it again. Printing a new `pip` success message does not unload the old Python
module. In a shared scientific environment, do not use `--ignore-installed`:
that option can replace unrelated dependency versions. Prefer the dedicated,
commit-pinned kernel in [Installation](install.md#testing-current-main-in-a-notebook).

Every maintained vignette begins by printing `cd.version_info()`. That makes a
rendered lesson auditable without confusing `0.1.0rc1` from PyPI with post-RC
source that intentionally retains the same version string.
