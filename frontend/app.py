from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from matchmaking_lab.markets import MARKETS


# ------------------------------------------------------------------
# Configurazione della pagina
# ------------------------------------------------------------------

st.set_page_config(
    page_title="Laboratorio di Matchmaking a Due Lati",
    layout="wide",
)

st.title("Laboratorio di Matchmaking a Due Lati")

st.caption(
    "Simulazione Monte Carlo ispirata al modello di Peng Shi (2023). "
    "Airbnb e Care.com rappresentano due mercati reali di riferimento; "
    "i valori delle preference densities sono calibrazioni sperimentali "
    "e non stime ottenute da dati proprietari delle piattaforme."
)


results_dir = ROOT / "results"


# ------------------------------------------------------------------
# Lettura dei risultati
# ------------------------------------------------------------------

def load_csv(name: str) -> pd.DataFrame | None:
    path = results_dir / name

    if path.exists():
        return pd.read_csv(path)

    return None


def baseline_line(fig, market_key: str) -> None:
    spec = MARKETS[market_key]

    x = (
        spec.baseline_d_j
        if market_key == "airbnb"
        else spec.baseline_d_i
    )

    fig.add_vline(
        x=x,
        line_dash="dash",
        annotation_text="baseline",
    )


# ------------------------------------------------------------------
# Sezioni dell'interfaccia
# ------------------------------------------------------------------

tab_scaling, tab_sensitivity, tab_efficiency, tab_method = st.tabs(
    [
        "Scaling del mercato",
        "Analisi di sensibilità",
        "Confronto di efficienza",
        "Metodologia",
    ]
)


summary = load_csv("experiment_summary.csv")
efficiency = load_csv("experiment_efficiency.csv")


# ------------------------------------------------------------------
# Controllo dei risultati disponibili
# ------------------------------------------------------------------

if summary is None:

    st.info(
        "Non sono ancora disponibili risultati della simulazione. "
        "Dalla cartella principale del progetto esegui "
        "`python -m matchmaking_lab.cli --preset quick` "
        "per un test veloce oppure "
        "`python -m matchmaking_lab.cli --preset standard --workers 4` "
        "per la simulazione principale."
    )

else:

    market_label_to_key = {
        spec.label: key
        for key, spec in MARKETS.items()
    }


    # ==============================================================
    # SCALING DEL MERCATO
    # ==============================================================

    with tab_scaling:

        st.subheader(
            "Scaling a preference densities fisse"
        )

        st.write(
            "In questa sezione viene considerata soltanto la configurazione "
            "di riferimento di ciascun mercato. I valori di $d_I$ e $d_J$ "
            "rimangono fissi mentre varia $n$, permettendo di isolare "
            "l'effetto della dimensione del mercato."
        )

        selected_label = st.selectbox(
            "Mercato",
            list(market_label_to_key),
            key="scaling_market",
        )

        selected_key = market_label_to_key[
            selected_label
        ]

        filtered = summary[
            (summary["market_key"] == selected_key)
            & (summary["is_baseline"] == True)
        ].copy()

        if not filtered.empty:

            d_i = filtered["d_I"].iloc[0]
            d_j = filtered["d_J"].iloc[0]

            st.caption(
                f"Configurazione di riferimento: "
                f"d_I = {d_i:.2f}, d_J = {d_j:.2f}"
            )

        filtered["ci95_half_interactions"] = (
            filtered["ci95_high_interactions"]
            - filtered["mean_interactions"]
        )

        filtered["ci95_half_welfare"] = (
            filtered["ci95_high_welfare_ratio"]
            - filtered["mean_welfare_ratio"]
        )


        c1, c2 = st.columns(2)


        with c1:

            fig = px.line(
                filtered,
                x="n",
                y="mean_interactions",
                error_y="ci95_half_interactions",
                color="strategy",
                markers=True,
                title=(
                    "Interazioni medie per cliente "
                    "al variare della dimensione del mercato"
                ),
                labels={
                    "n": "Dimensione del mercato n",
                    "mean_interactions":
                        "Interazioni medie per cliente",
                    "strategy": "Strategia",
                },
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )


        with c2:

            fig = px.line(
                filtered,
                x="n",
                y="mean_welfare_ratio",
                color="strategy",
                markers=True,
                title=(
                    "Welfare ratio medio "
                    "al variare della dimensione del mercato"
                ),
                labels={
                    "n": "Dimensione del mercato n",
                    "mean_welfare_ratio":
                        "Welfare ratio medio",
                    "strategy": "Strategia",
                },
            )

            fig.update_yaxes(
                range=[0, 1.02]
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )


        st.dataframe(
            filtered[
                [
                    "n",
                    "d_I",
                    "d_J",
                    "strategy",
                    "mean_interactions",
                    "ci95_low_interactions",
                    "ci95_high_interactions",
                    "mean_welfare_ratio",
                    "ci95_low_welfare_ratio",
                    "ci95_high_welfare_ratio",
                    "mean_match_rate",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )


    # ==============================================================
    # ANALISI DI SENSIBILITÀ
    # ==============================================================

    with tab_sensitivity:

        st.subheader(
            "Sensibilità rispetto alle preference densities"
        )

        st.write(
            "In questa sezione la dimensione del mercato viene mantenuta "
            "fissa, mentre vengono modificati i valori delle preference "
            "densities. L'obiettivo è osservare come cambia la performance "
            "delle strategie quando le preferenze diventano più o meno "
            "facili da descrivere."
        )


        selected_label = st.selectbox(
            "Mercato",
            list(market_label_to_key),
            key="sensitivity_market",
        )

        selected_key = market_label_to_key[
            selected_label
        ]


        available_n = sorted(
            summary[
                summary["market_key"]
                == selected_key
            ]["n"].unique()
        )


        selected_n = st.select_slider(
            "Dimensione del mercato n",
            options=available_n,
            value=available_n[
                len(available_n) // 2
            ],
        )


        filtered = summary[
            (summary["market_key"] == selected_key)
            & (summary["n"] == selected_n)
        ].copy()


        x_title = (
            MARKETS[selected_key]
            .sensitivity_parameter
        )


        filtered["ci95_half_interactions"] = (
            filtered["ci95_high_interactions"]
            - filtered["mean_interactions"]
        )

        filtered["ci95_half_welfare"] = (
            filtered["ci95_high_welfare_ratio"]
            - filtered["mean_welfare_ratio"]
        )


        c1, c2 = st.columns(2)


        with c1:

            fig = px.line(
                filtered,
                x="sensitivity_value",
                y="mean_interactions",
                error_y="ci95_half_interactions",
                color="strategy",
                markers=True,
                title=(
                    f"Sensibilità del costo di comunicazione "
                    f"per n = {selected_n}"
                ),
                labels={
                    "sensitivity_value":
                        x_title,
                    "mean_interactions":
                        "Interazioni medie per cliente",
                    "strategy":
                        "Strategia",
                },
            )

            baseline_line(
                fig,
                selected_key,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )


        with c2:

            fig = px.line(
                filtered,
                x="sensitivity_value",
                y="mean_welfare_ratio",
                error_y="ci95_half_welfare",
                color="strategy",
                markers=True,
                title=(
                    f"Sensibilità della qualità del matching "
                    f"per n = {selected_n}"
                ),
                labels={
                    "sensitivity_value":
                        x_title,
                    "mean_welfare_ratio":
                        "Welfare ratio medio",
                    "strategy":
                        "Strategia",
                },
            )

            baseline_line(
                fig,
                selected_key,
            )

            fig.update_yaxes(
                range=[0, 1.02]
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )


        st.dataframe(
            filtered[
                [
                    "scenario",
                    "d_I",
                    "d_J",
                    "strategy",
                    "mean_interactions",
                    "mean_welfare_ratio",
                    "mean_match_rate",
                    "centralized_sufficient_condition",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )


    # ==============================================================
    # CONFRONTO DI EFFICIENZA
    # ==============================================================

    with tab_efficiency:

        st.subheader(
            "Efficienza comunicativa a parità di qualità dell'outcome"
        )

        st.write(
            "Una strategia viene considerata efficiente soltanto quando "
            "raggiunge un welfare ratio almeno pari a 0.95 e utilizza "
            "il minor numero di interazioni tra le strategie ammissibili "
            "nella stessa replica Monte Carlo. In caso di parità, il credito "
            "viene suddiviso equamente tra le strategie coinvolte."
        )


        if (
            efficiency is None
            or efficiency.empty
        ):

            st.info(
                "Non è disponibile un riepilogo "
                "dell'efficienza comunicativa."
            )

        else:

            selected_label = st.selectbox(
                "Mercato",
                list(market_label_to_key),
                key="efficiency_market",
            )

            selected_key = (
                market_label_to_key[
                    selected_label
                ]
            )


            available_n = sorted(
                efficiency[
                    efficiency["market_key"]
                    == selected_key
                ]["n"].unique()
            )


            selected_n = st.select_slider(
                "Dimensione del mercato n",
                options=available_n,
                value=available_n[
                    len(available_n) // 2
                ],
                key="efficiency_n",
            )


            filtered = efficiency[
                (
                    efficiency["market_key"]
                    == selected_key
                )
                & (
                    efficiency["n"]
                    == selected_n
                )
            ].copy()


            fig = px.line(
                filtered,
                x="sensitivity_value",
                y="efficient_share",
                color="strategy",
                markers=True,
                title=(
                    "Quota di efficienza comunicativa "
                    f"per n = {selected_n}"
                ),
                labels={
                    "sensitivity_value":
                        MARKETS[
                            selected_key
                        ].sensitivity_parameter,
                    "efficient_share":
                        "Quota di efficienza",
                    "strategy":
                        "Strategia",
                },
            )


            baseline_line(
                fig,
                selected_key,
            )

            fig.update_yaxes(
                range=[0, 1.02]
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )


            st.dataframe(
                filtered,
                use_container_width=True,
                hide_index=True,
            )


    # ==============================================================
    # METODOLOGIA
    # ==============================================================

    with tab_method:

        st.markdown(
            r"""
### Disegno sperimentale

La simulazione è costruita come un unico esperimento. Per ogni configurazione delle preference densities vengono analizzate le stesse dimensioni di mercato, mentre la baseline rappresenta uno dei punti di riferimento all'interno dell'analisi.

- **Airbnb / short-term rentals:** $d_I = 0.10$ rimane fisso, mentre
  $d_J \in \{0.20, 0.40, 0.60, 0.80, 1.00\}$. La configurazione di riferimento è $(0.10, 0.80)$.

- **Care.com / childcare:** le preference densities dei due lati variano insieme,
  $d_I = d_J \in \{0.02, 0.05, 0.10, 0.20, 0.40\}$. La configurazione di riferimento è $(0.02, 0.02)$.

I valori di $d_I$ e $d_J$ non sono stime ricavate da dati proprietari di Airbnb o Care.com. Sono parametri sperimentali utilizzati per rappresentare diversi livelli di descrivibilità delle preferenze nei due mercati.


### Come viene condotto l'esperimento

Quando varia la dimensione del mercato $n$, i valori di $d_I$ e $d_J$ restano fissi. In questo modo possiamo osservare l'effetto della crescita del mercato senza modificarne contemporaneamente la struttura informativa.

La sensitivity analysis segue la logica opposta: fissiamo $n$ e facciamo variare le preference densities. Possiamo quindi osservare separatamente come cambia il comportamento delle strategie quando le preferenze diventano progressivamente più facili o più difficili da descrivere.


### Simulazione Monte Carlo

Per ogni replica viene generato un mercato e, sullo stesso insieme di benefici e costi, vengono eseguiti tutti e quattro i protocolli di matchmaking. In questo modo il confronto tra le strategie avviene nelle stesse condizioni.

Anche il confronto tra diversi livelli di preference density utilizza la stessa base casuale per una determinata dimensione del mercato e replica. Questo riduce la variabilità dovuta alla generazione casuale e rende più leggibili le differenze tra gli scenari.


### Cosa misuriamo

Per ogni strategia osserviamo:

- il numero medio di interazioni per cliente;
- il welfare ratio rispetto al matching ottimale con informazione perfetta;
- il match rate;
- gli intervalli di confidenza al 95%.

Consideriamo inoltre l'efficienza comunicativa. Tra le strategie che raggiungono un welfare ratio almeno pari a $0.95$, osserviamo quale riesce a ottenere il risultato utilizzando meno interazioni. Se più strategie ottengono lo stesso risultato, il credito viene suddiviso tra loro.


### Obiettivo

L'obiettivo della simulazione è osservare numericamente i meccanismi discussi da Shi (2023), concentrandosi sul rapporto tra preference density, quantità di comunicazione richiesta e qualità del matching.

L'esperimento non cerca invece di riprodurre le dimostrazioni teoriche dei lower bound della communication complexity in bits presentate nel paper, che richiedono strumenti di information theory.
"""
        )