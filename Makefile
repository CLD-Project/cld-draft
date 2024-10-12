cld-map:
	cd maps; python base-map.py

cld-workflow:
	cd workflow; python get_references.py phom1236
	cd workflow; python get_references.py mans1258

cld-test-corpus:
	cd glottolog; python explore.py


install-requirements:
	pip install -r requirements.txt
