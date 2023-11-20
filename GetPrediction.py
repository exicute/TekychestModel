#1)Подготовка данных для предсказания модели
#2)Предсказание
#3)Выгрузка данных в таблицу


from sklearn import tree
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
import joblib
import pygsheets
import datetime



class predictor():


    def __init__(self):
        pass


    def prework(self):
        #авторизация; выгрузка данных
        pass


    def make_result_table_work(self, rieltor_df, act_day, act_month, act_year):
        results_df = pd.DataFrame(columns=['id', 'name'])
        rieltors_copy = rieltor_df.copy()

        #rieltors_copy = rieltors_copy.loc[rieltors_copy['Дата увольнения']=='null']
        #rieltors_copy = rieltors_copy.drop(columns={'Дата увольнения'})
        rieltors_copy['Дата приема на работу'] = pd.to_datetime(rieltors_copy['Дата приема на работу'], dayfirst=True)

        date_ser = pd.Series(np.full((rieltors_copy.shape[0]), datetime.date(act_year, act_month, act_day)))
        rieltors_copy['стаж'] = pd.to_datetime(date_ser)-rieltors_copy['Дата приема на работу']

        #results_df = rieltors_copy.loc[rieltors_copy['стаж']//np.timedelta64(1, 'M')>=6]
        results_df = rieltors_copy
        results_df = results_df.rename(columns={'Код сотрудника':'id', 'ФИО сотрудника':'name'})
        results_df['id'] = results_df['id'].astype('string')

        return results_df
    

    def make_tables_coef_dict(self, ds_dict, month_to_month_num, id_names, table_work_fire_name):

        def calculate_per_month_column(table, month_to_month_num, id_names):
            id_name = ''
            for column in table.columns:
                if column in id_names:
                    id_name = column
                else:
                    continue

            if id_name == '':
                return 'Добавьте название колонки с кодом в список'

            work_table = table.copy()
            if 'Итого' in list(work_table.iloc[-1]):
                work_table = work_table.drop(work_table.iloc[-1].name)

            all_month_col = work_table.columns[::-1][:2*month_to_month_num]
            fir_month_col = work_table.columns[::-1][:month_to_month_num]
            sec_month_col = work_table.columns[::-1][month_to_month_num:2*month_to_month_num]

            work_table = work_table[all_month_col].replace('', '0')
            try:
                work_table[all_month_col] = work_table[all_month_col].astype(float)
            except ValueError:
                for col in work_table[all_month_col].columns:
                    work_table[col] = work_table[col].apply(lambda x: float(x.replace(',', '.')))

            fir_col_sum = work_table.loc[:, fir_month_col].sum(axis=1)
            sec_col_sum = work_table.loc[:, sec_month_col].sum(axis=1)
            work_table['coef'] = pd.eval('fir_col_sum+sec_col_sum')
            work_table['id'] = table[id_name].astype('string').copy()

            return work_table    
        
        coef_dict = {}

        #сделать расчет коэф. для всех возможных месяцев до заданного месяца month_indx
        for key, value in ds_dict.items():
            if key!=table_work_fire_name:
                coef_dict[key] = pd.DataFrame()
                coef_dict[key] = calculate_per_month_column(value, month_to_month_num, id_names)

        return coef_dict
    

    def make_dataset(result_table, datasets_dict, result_table_on, table_on, using_join):

        def inside_dataset(result_table, table, result_table_on, table_on, results_table_name, table_name, using_join):
            full_dataset = result_table.merge(table, left_on=result_table_on, right_on=table_on, how=using_join, suffixes=(f'_{results_table_name}', f'_{table_name}'))
            return full_dataset


        full_dataset = result_table

        temp_key = ''
        for key, value in datasets_dict.items():
            full_dataset = inside_dataset(full_dataset, value[['coef', 'id']], 'id', 'id', temp_key, key, using_join)
            temp_df = full_dataset
            temp_key = key

        return full_dataset