import json
import psycopg2
from flask import Flask, render_template, request


app = Flask(__name__, static_folder='./webapp/static/', template_folder='./webapp/templates')


def get_db_connection():
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="ratrat",
        host="localhost"
    )
    return conn


@app.route("/")
def main():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM poi_data.city;")
    cities = cur.fetchall()
    cur.close()
    conn.close()

    city_images = {
        "Berlin, Germany": "berlin.jpg",
        "Stockholm, Sweden": "stockholm.jpg",
        "Klaipeda, Lithuania": "klaipeda.jpg",
        "Paris, France": "paris.jpg"
    }

    return render_template('main.html', cities=cities, city_images=city_images)


@app.route("/city/<int:city_id>")
def citylist(city_id):  
    sort_by = request.args.get('sort_by', 'relevance_score')
    conn = get_db_connection()
    cur = conn.cursor() 

    cur.execute("SELECT name FROM poi_data.city WHERE city_id = %s;", (city_id,))
    city_name = cur.fetchone()[0]

    sort_column = 'relevance_score'
    if sort_by == 'view_count':
        sort_column = 'view_count'
    elif sort_by == 'page_size':
        sort_column = 'page_size'
    elif sort_by == 'image_count':
        sort_column = 'image_count'
    elif sort_by == 'link_count':
        sort_column = 'link_count'

    cur.execute(f"""
        SELECT place_id, name, image, {sort_column}  
        FROM poi_data.place 
        WHERE city_id = %s 
        ORDER BY {sort_column} DESC;
    """, (city_id,))
    places = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('citylist.html', city_name=city_name, city_id=city_id, sort_by=sort_by, places=places)




@app.route("/place/<int:place_id>")
def city(place_id):
    conn = get_db_connection()
    cur = conn.cursor()


    cur.execute("""
        SELECT p.place_id, p.name, p.latitude, p.longitude, p.city_id, p.type, p.image, 
               p.view_count, p.page_size, p.link_count, p.image_count, p.relevance_score, 
            c.name AS city_name
        FROM poi_data.place p
        JOIN poi_data.city c ON p.city_id = c.city_id
        WHERE p.place_id = %s;
    """, (place_id,))
    place = cur.fetchone()

    city_country = place[12].split(', ')
    city_name = city_country[0]
    country_name = city_country[1] if len(city_country) > 1 else 'Unknown'
    cur.execute("""
        SELECT sp.similar_place_id, p.name, p.image, sp.sim_score 
        FROM poi_data.similar_places_data sp
        JOIN poi_data.place p ON sp.similar_place_id = p.place_id
        WHERE sp.main_place_id = %s AND p.city_id = %s
        ORDER BY sp.sim_score DESC;
    """, (place_id, place[4]))
    similar_places_by_data_same_city = cur.fetchall()


    cur.execute("""
        SELECT sp.similar_place_id, p.name, p.image, sp.sim_score 
        FROM poi_data.similar_places_data sp
        JOIN poi_data.place p ON sp.similar_place_id = p.place_id
        WHERE sp.main_place_id = %s AND p.city_id != %s
        ORDER BY sp.sim_score DESC;
    """, (place_id, place[4]))
    similar_places_by_data_other_cities = cur.fetchall()


    cur.execute("""
        SELECT sp.similar_place_id, p.name, p.image, sp.sim_score 
        FROM poi_data.similar_places_colors sp
        JOIN poi_data.place p ON sp.similar_place_id = p.place_id
        WHERE sp.main_place_id = %s AND p.city_id = %s
        ORDER BY sp.sim_score DESC;
    """, (place_id, place[4]))
    similar_places_by_colors_same_city = cur.fetchall()


    cur.execute("""
        SELECT sp.similar_place_id, p.name, p.image, sp.sim_score 
        FROM poi_data.similar_places_colors sp
        JOIN poi_data.place p ON sp.similar_place_id = p.place_id
        WHERE sp.main_place_id = %s AND p.city_id != %s
        ORDER BY sp.sim_score DESC;
    """, (place_id, place[4]))
    similar_places_by_colors_other_cities = cur.fetchall()

    cur.close()
    conn.close()
    return render_template(
        'city.html',
        place=place,
        city_name=city_name,
        country_name=country_name,
        similar_places_by_data_same_city=similar_places_by_data_same_city,
        similar_places_by_colors_same_city=similar_places_by_colors_same_city,
        similar_places_by_colors_other_cities=similar_places_by_colors_other_cities)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
