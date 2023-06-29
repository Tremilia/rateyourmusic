from rateyourmusic.api_rateyourmusic import process_main_link

if __name__ == '__main__':
    main_links = [
        # 'https://rateyourmusic.com/charts/top/musicvideo/all-time/'
    ]
    for ml in main_links:
        process_main_link(ml)