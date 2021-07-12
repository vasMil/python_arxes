import sys
import pickle
import web_scraping as ws
import load_data as ld
import proj_sql as ps
import proj_gui as gui


def main():
    # # The titles of the datasets I want to download
    ws_argv = "Arrivals of residents/non-residents at tourist accommodation establishments", \
          "Nights spent at tourist accommodation establishments by residents/non-residents"
    dflag = 0
    # Download if requested (first argument must be download)
    if len(sys.argv) > 1 and sys.argv[1] == "download":
        dflag = 1
        filenames = ws.get_files(ws_argv)
        # save the filenames in a pickle file so I may retrieve later
        file = open("my_pickle.txt", 'wb')
        pickle.dump(filenames, file)
        file.close()

    # Update the database with the new data, if requested (second, or first argument sql)
    if (len(sys.argv) > 2 and dflag == 1 and sys.argv[2] == "sql") or sys.argv[1] == "sql":
        dflag += 1
        mycursor = ps.connect_mysql()
        ps.create_default_tables(mycursor)
        ps.load_tables(mycursor, "Web_Scraping_Results/tin00174.csv")
        ps.load_tables(mycursor, "Web_Scraping_Results/tin00175.csv")

    # load the filenames from pickle file
    file = open("my_pickle.txt", 'rb')
    filenames = pickle.load(file)
    file.close()
    path = "Web_Scraping_Results/"
    # # DEBUG CODE:
    # # # If less than 3 arguments get to default (ELLADA, CYPRUS)
    # # # (There should always be at least 3 arguments arg0->main.py arg1-> requested country arg2-> req. country)
    # # # I only did this so I make compile easier with Shift + F10
    # # if len(sys.argv) < 3 and flag == 0:
    # #     print("Defaulting to EL, CY...")
    # #     args = ["EL", "CY"]
    # # else:
    # #     args = sys.argv[flag+1:]
    args = sys.argv[dflag+1:]
    # # Loop for each country
    for geo in args:
        cnt = 0
        # Loop for each dataset title
        for argv in ws_argv:
            country = ld.CountryStats(geo, path+filenames[cnt]+".csv", 2008, 2011, argv)
    #         # DEBUG_CODE:
    #         # print(f"\t{argv} in {country.country}")
    #         # print("Foreign Stats:")
    #         # country.foreign.print_stats()
    #         # print("Native Stats:")
    #         # country.native.print_stats()
    #         # print("Total Stats:")
    #         # country.total.print_stats()
            country.plot_me()
            country.request_plot("Total")
            country.request_plot("Foreigners")
            cnt += 1
    # gui.main_window(filenames, ws_argv)


if __name__ == "__main__":
    main()
