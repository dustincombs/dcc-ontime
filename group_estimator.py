from sklearn.base import BaseEstimator, ClassifierMixin, RegressorMixin
from sklearn.pipeline import Pipeline
from sklearn.ensemble import HistGradientBoostingClassifier
import pandas as pd

class GroupbyEstimator(BaseEstimator, ClassifierMixin):
    
    def __init__(self, column, model_factory):
        self.column = column
        self.model_factory = model_factory
        self.models = {}
        
    def fit(self, X, y):
        X['target'] = y
        for name, group in X.groupby(self.column):
            self.models[name] = self.model_factory()
            self.models[name].fit(group, group['target'])
        return self

    def predict_proba(self, X):
        
        pos = pd.Series(data=0.0,index=X.index,dtype='float')
        neg = pd.Series(data=0.0,index=X.index,dtype='float')
        groups = X.groupby(self.column)
        for name, group in groups:
            indices = groups.indices[name]
            pos.loc[indices] = self.models[name].predict_proba(group)[:,0]
            neg.loc[indices] = self.models[name].predict_proba(group)[:,-1]
        return pd.concat([pos, neg],axis=1).values


class ColumnSelector(BaseEstimator, RegressorMixin):

    def __init__(self, cols):
        self.cols = cols

    def fit(self, X, y=None):
        # This transformer doesn't need to learn anything about the data,
        # so it can just return self without any further processing
        return self
    
    def transform(self, df):
        return df[self.cols]

def hgbc_factory():
    cols = ['hour','dayofweek','weekofyear','flighttime']
    # ct = ColumnTransformer([('select','passthrough',cols)],remainder='drop') 
    ct = ColumnSelector(cols)
    return Pipeline([('col_select',ct),('hgbc',HistGradientBoostingClassifier())])