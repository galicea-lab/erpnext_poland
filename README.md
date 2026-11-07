### ERPNext Poland

ErpNext for Poland

Details (in Polish): description.md

Demo: https://erpnext.transmem.pl/

login: demo/transmem


### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch version-16
bench install-app erpnext_poland
```

### Translations

Sources are English; Polish is delivered by `erpnext_poland/translations/pl.csv`
(key: English text, value: Polish translation). Labels, descriptions, button
captions and messages are wrapped in `_()` so the Polish UI keeps working, and
Select options are translated on display as well (the stored value stays
English).

When you add a user-facing string, add its Polish translation to `pl.csv`.

Migrating an older site: `bench --site <site> migrate` runs
`patches/v1_0/translate_ksef_options.py`, which rewrites the previously Polish
values that are stored in documents - the KSeF status of Sales/Purchase Invoice,
the technical `BRAK` GTU value on Item and the item source setting of Polish
Accounting Settings.

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/erpnext_poland
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

gpl-3.0
