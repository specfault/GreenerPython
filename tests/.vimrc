set nocompatible

augroup createfilegroup
	au!
	autocmd BufNewFile *.py 
				\ let tmp = expand('%:p') |
				\ :bd |
				\ let res = system('create_file.py ' . tmp) |
				\ :execute 'normal! :e ' . res
augroup END
