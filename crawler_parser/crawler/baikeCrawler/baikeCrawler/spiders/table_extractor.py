'''
@File    :  tableExtractor.py
@Author  :  Vector
@Date    :  2021/8/24--14:44
@Desc    :  extract table from html
@PARAMs  :
@RETURN  :
'''
from bs4 import BeautifulSoup, Tag
class tableExtractor(object):
    def __init__(self,input,id_=None,**kwargs):
        #传入的参数必须是bs4通过标签拿到的元素
        if not isinstance(input,str) and not isinstance(input,Tag):
            raise Exception("Unvalid input. Valid input: str, bs4.element.Tag")
        soup=BeautifulSoup(input,'html.parser').find() if isinstance(input,str) else input

        if soup.name == 'table':
            self._table=soup
        else:
            self._table=soup.find(id=id_)

        if 'transformer' in kwargs:
            self._transformer=kwargs['transformer']
        else:
            self._transformer=str
        self._output_list=[]
        self._output_dict={}

    def parse(self):
        self._output_list = []
        row_ind = 0
        col_ind = 0
        for row in self._table.find_all('tr'):
            # record the smallest row_span, so that we know how many rows
            # we should skip
            smallest_row_span = 1

            for cell in row.children:
                if cell.name in ('td', 'th'):
                    # check multiple rows
                    # pdb.set_trace()
                    row_span = int(cell.get('rowspan')) if cell.get('rowspan') else 1

                    # try updating smallest_row_span
                    smallest_row_span = min(smallest_row_span, row_span)

                    # check multiple columns
                    col_span = int(cell.get('colspan')) if cell.get('colspan') else 1

                    # find the right index
                    while True:
                        if self._check_cell_validity(row_ind, col_ind):
                            break
                        col_ind += 1

                    # insert into self._output
                    try:
                        self._insert(row_ind, col_ind, row_span, col_span, self._transformer(cell.get_text()))
                    except UnicodeEncodeError:
                        raise Exception('Failed to decode text; you might want to specify kwargs transformer=unicode')

                    # update col_ind
                    col_ind += col_span

            # update row_ind
            row_ind += smallest_row_span
            col_ind = 0
        if self._table.find('caption'):
            self._output_dict={
                "caption":self._table.find('caption').text,
                "tableData":self._output_list
            }
        else:
            self._output_dict={
                "caption": "noneName",
                "tableData": self._output_list
            }
        return self

    def return_list(self):
        return self._output_list

    def return_dict(self):
        return self._output_dict


    def _check_validity(self, i, j, height, width):
        """
        check if a rectangle (i, j, height, width) can be put into self.output
        """
        return all(self._check_cell_validity(ii, jj) for ii in range(i, i+height) for jj in range(j, j+width))

    def _check_cell_validity(self, i, j):
        """
        check if a cell (i, j) can be put into self._output
        """
        if i >= len(self._output_list):
            return True
        if j >= len(self._output_list[i]):
            return True
        if self._output_list[i][j] is None:
            return True
        return False

    def _insert(self, i, j, height, width, val):
        # pdb.set_trace()
        for ii in range(i, i+height):
            for jj in range(j, j+width):
                self._insert_cell(ii, jj, val)

    def _insert_cell(self, i, j, val):
        while i >= len(self._output_list):
            self._output_list.append([])
        while j >= len(self._output_list[i]):
            self._output_list[i].append(None)

        if self._output_list[i][j] is None:
            self._output_list[i][j] = val