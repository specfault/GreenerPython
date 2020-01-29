set nocompatible

augroup createfilegroup
	au!
	autocmd BufNewFile test_*.py 
				\ let tmp = expand('%:p') |
				\ :bd |
				\ let res = system('create_file.py ' . fnameescape(tmp)) |
				\ :execute 'normal! :e ' . res
augroup END

augroup savefilegroup
	au!
	autocmd BufWritePost test_*.py
				\ let tmp = expand('%:p') |
				\ let res = system('save_file.py ' . tmp) |
				\ :e!
augroup END
