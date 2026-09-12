import pandas as pd
import statsmodels.api as sm

from statsmodels.tsa.api import VAR
from statsmodels.tsa.ardl import ARDL


def prepare_model_data(df):

    variables = [
        "GDP_Growth",
        "Consumption_Growth",
        "Investment_Growth",
        "Bank_Rate",
        "CPI",
        "Unemployment"
    ]

    data = (
        df[variables]
        .replace(
            [float("inf"), -float("inf")],
            pd.NA
        )
        .dropna()
    )

    return data


# ============================================================
# OLS
# ============================================================

def run_ols(df):

    data = df[
        [
            "GDP_Growth",
            "Bank_Rate_Change",
            "Bank_Rate_Change_Lag1",
            "Bank_Rate_Change_Lag2",
            "CPI",
            "Unemployment"
        ]
    ].dropna()

    y = data[
        "GDP_Growth"
    ]

    X = data[
        [
            "Bank_Rate_Change",
            "Bank_Rate_Change_Lag1",
            "Bank_Rate_Change_Lag2",
            "CPI",
            "Unemployment"
        ]
    ]

    X = sm.add_constant(X)

    model = sm.OLS(
        y,
        X
    ).fit(
        cov_type="HC1"
    )

    return model


# ============================================================
# ARDL
# ============================================================

def run_ardl(df):

    data = df[
        [
            "GDP_Growth",
            "Bank_Rate",
            "CPI",
            "Unemployment"
        ]
    ].dropna()

    model = ARDL(
        data["GDP_Growth"],
        lags=4,
        exog=data[
            [
                "Bank_Rate",
                "CPI",
                "Unemployment"
            ]
        ],
        order=2,
        trend="c"
    )

    results = model.fit()

    return results


# ============================================================
# VAR
# ============================================================

def run_var(df):

    variables = [
        "GDP_Growth",
        "CPI",
        "Bank_Rate"
    ]

    data = (
        df[variables]
        .dropna()
    )

    model = VAR(
        data
    )

    results = model.fit(
        maxlags=4,
        ic="aic"
    )

    return results


# ============================================================
# IMPULSE RESPONSE
# ============================================================

def run_impulse_response(
    var_results,
    periods=12
):

    irf = var_results.irf(
        periods
    )

    return irf