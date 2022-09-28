import pandas as pd
import streamlit as st
import connectToSQL as c
import plotly.graph_objects as go


def topTimes(wcaId):
    """
    Function used to calculate a competitors top times (single or average)
    for a specfied event.
    Args:
        wcaId - inputted WCA ID by the user to find statistic for specific ID
    Returns:
        df - dataframe containing the statistic with the inputted specifications
        tableTitle - title for the table to be displayed on app
    """

    # Options for event
    event_query = "SELECT name FROM Events"
    event_df = pd.read_sql(event_query, c.engine)

    # Select average of single
    timeType = st.sidebar.radio(
        "Single or average?", 
        ('Single', 'Average')
    )

    # Select event and number of results
    event = st.sidebar.selectbox("Select WCA event", event_df)
    num_results = st.sidebar.slider("Select number of results to display", 0, 100, 10)

    # Single is selected
    if timeType == 'Single':
        
        # edge case for FMC event
        if event == '3x3x3 Fewest Moves':
            eventTime_query = f"""
            SELECT DISTINCT
                CASE c.solve
                    WHEN 'value1' THEN value1
                    WHEN 'value2' THEN value2
                    WHEN 'value3' THEN value3
                    WHEN 'value4' THEN value4
                    WHEN 'value5' THEN value5
                END AS Moves,
                RIGHT(c.solve, 1) AS Solve_Num,
                CONCAT(c.month, '-', c.day, '-', c.year) AS Date,
                c.cityName AS Location,
                r.competitionId AS Competition,
                rt.name AS Round
            FROM Results AS r
            JOIN Competitions AS c
            ON r.competitionId = c.id
            JOIN RoundTypes AS rt
            ON rt.id = r.roundTypeId
            JOIN Events AS e
            ON r.eventId = e.id
            CROSS JOIN (
                SELECT 'value1' AS solve
                UNION ALL SELECT 'value2'
                UNION ALL SELECT 'value3'
                UNION ALL SELECT 'value4'
                UNION ALL SELECT 'value5') c
            WHERE r.personId = '{wcaId}' AND e.name = '{event}'
                AND CASE c.solve
                    WHEN 'value1' THEN value1
                    WHEN 'value2' THEN value2
                    WHEN 'value3' THEN value3
                    WHEN 'value4' THEN value4
                    WHEN 'value5' THEN value5
                END > 0
            ORDER BY 1
            LIMIT {num_results}
            """

        else:
            # event time query for single
            eventTime_query = f"""
            SELECT 
                CASE 
                    WHEN t.Time < 6000 THEN ROUND(t.Time / 100, 2)
                    ELSE RIGHT(SEC_TO_TIME(ROUND(t.Time / 100, 2)), 7)
                END AS Time,
                t.Solve_Num, t.Date, t.Location, t.Competition, t.Round
            FROM (
                SELECT DISTINCT
                    CASE c.solve
                        WHEN 'value1' THEN value1
                        WHEN 'value2' THEN value2
                        WHEN 'value3' THEN value3
                        WHEN 'value4' THEN value4
                        WHEN 'value5' THEN value5
                    END AS Time,
                    RIGHT(c.solve, 1) AS Solve_Num,
                    CONCAT(c.month, '-', c.day, '-', c.year) AS Date,
                    c.cityName AS Location,
                    r.competitionId AS Competition,
                    rt.name AS Round
                FROM Results AS r
                JOIN Competitions AS c
                ON r.competitionId = c.id
                JOIN RoundTypes AS rt
                ON rt.id = r.roundTypeId
                JOIN Events AS e
                ON r.eventId = e.id
                CROSS JOIN (
                    SELECT 'value1' AS solve
                    UNION ALL SELECT 'value2'
                    UNION ALL SELECT 'value3'
                    UNION ALL SELECT 'value4'
                    UNION ALL SELECT 'value5') c
                WHERE r.personId = '{wcaId}' AND e.name = '{event}'
                    AND CASE c.solve
                        WHEN 'value1' THEN value1
                        WHEN 'value2' THEN value2
                        WHEN 'value3' THEN value3
                        WHEN 'value4' THEN value4
                        WHEN 'value5' THEN value5
                    END > 0
                ORDER BY 1
                LIMIT {num_results}) t
                """

    # Average is selected
    else:

        # event time query for average
        eventTime_query = f"""
        SELECT 
            CASE 
                WHEN t.average < 6000 THEN ROUND(t.average / 100, 2)
                ELSE RIGHT(SEC_TO_TIME(ROUND(t.average / 100, 2)), 7)
            END AS Time,	
            t.Date, t.Location, t.Competition, t.Round
        FROM (
            SELECT DISTINCT
                r.average AS average,
                CONCAT(c.month, '-', c.day, '-', c.year) AS Date,
                c.cityName AS Location,
                r.competitionId AS Competition,
                rt.name AS Round
            FROM Results AS r
            JOIN Competitions AS c
            ON r.competitionId = c.id
            JOIN Events AS e
            ON r.eventId = e.id
            JOIN RoundTypes AS rt
            ON rt.id = r.roundTypeId
            WHERE r.personId = '{wcaId}' 
                AND e.name = '{event}'
                AND r.average > 0
            ORDER BY 1) t
        LIMIT {num_results};
        """

    # Take in query
    df = pd.read_sql(eventTime_query, c.engine)

    # Set table title
    tableTitle = ('Top ' + event + ' single times')

    return df, tableTitle

    # If average is selected


def medalCount(wcaId):
    """
    Function used to calculate a competitors medal count by event and overall.
    Args:
        wcaId - inputted WCA ID by the user to find statistic for specific ID
    Returns:
        df - dataframe containing the statistic with the inputted specifications
    """

    # medal count query
    medal_query = f"""
    SELECT 
        Event, 
        CAST(t.gold AS SIGNED) AS Gold, 
        CAST(t.silver AS SIGNED) AS Silver, 
        CAST(t.bronze AS SIGNED) AS Bronze
    FROM (
        SELECT 
            'Overall' AS event,
            SUM(CASE WHEN r.pos = 1 THEN 1 ELSE 0 END) AS gold,
            SUM(CASE WHEN r.pos = 2 THEN 1 ELSE 0 END) AS silver,
            SUM(CASE WHEN r.pos = 3 THEN 1 ELSE 0 END) AS bronze
        FROM Results as r
        WHERE r.roundTypeId IN ('f', 'c', 'b') 
            AND r.personId = '{wcaId}'
            AND r.best > 0
        UNION ALL
        SELECT * FROM
            (SELECT 
                e.name AS event,
                SUM(CASE WHEN r.pos = 1 THEN 1 ELSE 0 END) AS gold,
                SUM(CASE WHEN r.pos = 2 THEN 1 ELSE 0 END) AS silver,
                SUM(CASE WHEN r.pos = 3 THEN 1 ELSE 0 END) AS bronze
            FROM Results AS r
            JOIN Events AS e
            ON r.eventId = e.id
            WHERE r.roundTypeId IN ('f', 'c', 'b') 
                AND r.personId = '{wcaId}'
                AND r.best > 0
            GROUP BY 1
            ORDER BY 1) overall
            ) t"""
    
    # Take in query
    df = pd.read_sql(medal_query, c.engine)

    return df


def topLocations(wcaId):
    """
    Function used to calculate a competitors top locations (country, state, city)
    competed in.
    Args:
        wcaId - inputted WCA ID by the user to find statistic for specific ID
    Returns:
        df - dataframe containing the statistic with the inputted specifications
        tableTitle - title for the table to be displayed on app
    """
    # Select location type
    timeType = st.sidebar.radio(
        "Select location scope", 
        ('Country', 'US State', 'City')
    )

    if timeType == 'Country':

        tableTitle = 'Top countries competed in'

        location_query = f"""
        SELECT 
            RANK() OVER (ORDER BY t1.num_times_competed DESC) AS 'Rank',
	        t1.countries AS Country, 
            t1.num_times_competed AS Num_Times_Competed
        FROM
            (SELECT DISTINCT coun.name AS countries, COUNT(*) AS num_times_competed
            FROM
                (SELECT DISTINCT competitionId FROM Results 
                WHERE personId = '{wcaId}') AS r
            JOIN Competitions AS comp
            ON r.competitionId = comp.id
            JOIN Countries AS coun
            ON comp.countryId = coun.id
            GROUP BY 1
            ORDER BY 2 DESC) AS t1
        """

    elif(timeType == 'US State'):

        tableTitle = 'Top states competed in'

        location_query = f"""
        SELECT 
            RANK() OVER (ORDER BY t1.num_times_competed DESC) AS 'Rank',
	        t1.state AS State, 
            t1.num_times_competed AS Num_Times_Competed
        FROM
            (SELECT 
                SUBSTR(comp.cityName, LOCATE(',', comp.cityName) + 1, 99) AS state,
                COUNT(*) AS num_times_competed
            FROM
                (SELECT DISTINCT competitionId FROM Results 
                WHERE personId = '{wcaId}') AS r
            JOIN Competitions AS comp
            ON r.competitionId = comp.id
            JOIN Countries AS coun
            ON comp.countryId = coun.id
            WHERE coun.name = 'United States'
            GROUP BY 1
            ORDER BY 2 DESC) AS t1
        """

    elif(timeType == 'City'):

        tableTitle = 'Top cities competed in'

        location_query = f"""
        SELECT 
            RANK() OVER (ORDER BY t1.num_times_competed DESC) AS 'Rank',
	        t1.City,
            t1.num_times_competed AS Num_Times_Competed
        FROM (
            SELECT 
                comp.cityName AS City,
                COUNT(*) AS num_times_competed
            FROM
                (SELECT DISTINCT competitionId FROM Results 
                WHERE personId = '{wcaId}') AS r
            JOIN Competitions AS comp
            ON r.competitionId = comp.id
            JOIN Countries AS coun
            ON comp.countryId = coun.id
            GROUP BY 1
            ORDER BY 2 DESC) t1
        """

    df = pd.read_sql(location_query, c.engine)
    
    return df, tableTitle


def createTable(df, tableTitle, name):
    """
    Function used to create plotly table for the statistic.
    Args:
        df - dataframe containing data for the specified statistic
        tableTitle - specified title for the table
    Returns:
        df - dataframe containing the statistic with the inputted specifications
    """

    # Reference: https://stackoverflow.com/questions/61453796/better-way-to-plot-a-dataframe-on-a-plotly-table
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns),
        fill_color = 'light gray',
        align='left'),
        cells=dict(values=df.transpose().values.tolist(),
        align='left'))])
    
    fig.update_layout(title = tableTitle + ' for ' + name)

    fig


def main():
    
    st.title("WCA Profile Snapshot")

    # Select WCA ID and get name
    wcaId = st.sidebar.text_input("Enter your WCA ID", value = '')
    name = None

    # Find name for WCA ID
    try:
        name_query = f"SELECT name FROM Persons WHERE id = '{wcaId}'"
        name_df = pd.read_sql(name_query, c.engine)
        name = name_df['name'][0]
    except:
        st.write("Please enter a valid WCA ID.")

    # Select statistic
    stat = st.sidebar.selectbox(
        "Select statistic to view", 
        [
            'Top times',
            'Medal count by event',
            'Top locations competed in'
        ])

    if name is not None:

        # Top times statistic
        if stat == 'Top times':
            df, tableTitle = topTimes(wcaId)

        # Medal count statistic
        elif stat == 'Medal count by event':
            tableTitle = stat
            df = medalCount(wcaId)

        elif stat == 'Top locations competed in':
            df, tableTitle = topLocations(wcaId)

        # Create plotly table function 
        createTable(df, tableTitle, name)
 



if __name__ == '__main__':
    main()