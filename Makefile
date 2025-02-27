g:
	git add .
	git commit -m "$(arg)"
	git push -u origin main

%:
	@: