# Combined Sermon File

The master `branham_sermons.json` file (~150–200 MB) is too large to store in this repository.

**Download it from the [Releases page](https://github.com/philipatosam/bro-william-branham-sermon-library/releases).**

To generate it yourself from the individual JSONs:

```bash
python3 scripts/combine_sermons.py \
  --input output \
  --output combined/branham_sermons.json
```
