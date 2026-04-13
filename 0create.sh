source .env
cd $INST
source env/bin/activate

bench new-app erpnext_poland
bench --site $SITE install-app erpnext_poland

