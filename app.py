from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, flash
import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__, static_url_path='/static')

app.secret_key = 'asdf'
conn = psycopg2.connect(dbname='fntta', user='postgres', password='admin', host='localhost', port='5432')

app.config['UPLOAD_FOLDER'] = 'C:\\Users\\coding\\Desktop\\image_test' # Carpeta donde se guardarán las imágenes
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}  # Extensiones de archivo permitidas

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/image_test/<filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def index():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registros")
    registros = cursor.fetchall()
    #cursor.close()
    return render_template('index.html', registros=registros)

@app.route('/agregar', methods=['POST'])
def agregar():
    cursor = conn.cursor()
    nombre = request.form['nombre']
    apellido = request.form['apellido']
    ci = request.form['ci']
    nro_socio = request.form['nro_socio']
    depart = request.form['depart']
    locali = request.form['locali']
    imagen = request.files['imagen']
    # Aquí puedes guardar la imagen en el servidor o en una ubicación específica
    if imagen and allowed_file(imagen.filename):
        filename = secure_filename(imagen.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        imagen.save(filepath)
        cursor.execute("INSERT INTO registros (nombre, apellido, ci, nro_socio, depart, locali, imagen) VALUES (%s, %s, %s, %s, %s, %s, %s)", (nombre, apellido, ci, nro_socio, depart, locali, filename))
        conn.commit()
    else:
        # Manejar el caso cuando no se proporciona un archivo de imagen válido
        # Puedes mostrar un mensaje de error o realizar otras acciones
        pass

    #cursor.close()
    return redirect(url_for('index'))

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM registros WHERE id = %s", (id,))
    conn.commit()
   #cursor.close()
    return redirect(url_for('index'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    cursor = conn.cursor()
    if request.method == 'GET':
        cursor.execute("SELECT * FROM registros WHERE id = %s", (id,))
        registro = cursor.fetchone()
        #cursor.close()
        return render_template('editar.html', registro=registro)
    else:
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        ci = request.form['ci']
        nro_socio = request.form['nro_socio']
        depart = request.form['depart']
        locali = request.form['locali']
        imagen = request.files['imagen']
        cursor.execute("UPDATE registros SET nombre = %s, apellido = %s, ci = %s, nro_socio = %s, depart = %s, locali = %s, imagen = %s WHERE id = %s", (nombre, apellido, ci, nro_socio, depart, locali, imagen, id))
        conn.commit()
        #cursor.close()
        return redirect(url_for('index'))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/generar_informe')
def generar_informe():
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, apellido, ci, nro_socio, depart, locali, imagen FROM registros")
    registros = cursor.fetchall()
    #cursor.close()

    # Update each record with a URL for the image
    updated_registros = []
    for registro in registros:
        nombre, apellido, ci, nro_socio, depart, locali, imagen_path = registro
        imagen_filename = os.path.basename(imagen_path)  # Extracts the filename from the path
        imagen_url = url_for('uploaded_file', filename=imagen_filename)
        updated_registros.append((nombre, apellido, ci, nro_socio, depart, locali, imagen_url))

    return render_template('informe.html', registros=updated_registros)

@app.route('/generar_informe_carnes_pdf')
def generar_informe_carnes_pdf():
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, apellido, ci, nro_socio, depart, locali, imagen FROM registros")
    registros = cursor.fetchall()
    cursor.close()

    doc = SimpleDocTemplate("informe_carnes.pdf", pagesize=letter, rightMargin=72, leftMargin=72)
    elements = []
    styles = getSampleStyleSheet()
    style_normal = styles['Normal']
    style_heading = styles['Heading3']

    # Agregar un título o texto fijo al documento
    titulo_documento = Paragraph('<b>Carnet de Socio</b>', style_heading)
    elements.append(titulo_documento)
    elements.append(Spacer(1, 12))  # Añade un espacio después del título

    data = []
    for registro in registros:
        nombre, apellido, ci, nro_socio, depart, locali, imagen_path = registro
        nombre_completo = f"{nombre} {apellido}"

        # Crear los párrafos para los campos de texto
        titulo_nombre_completo = Paragraph(f'<b>Nombre completo:</b> {nombre_completo}', style_normal)
        titulo_ci = Paragraph(f'<b>CI:</b> {ci}', style_normal)
        titulo_nro_socio = Paragraph(f'<b>Nro Socio:</b> {nro_socio}', style_normal)
        titulo_depart = Paragraph(f'<b>Departamento:</b> {depart}', style_normal)
        titulo_locali = Paragraph(f'<b>Localidad:</b> {locali}', style_normal)

        # Tabla anidada para los campos de texto
        text_table = Table([
            [titulo_nombre_completo],
            [titulo_ci],
            [titulo_nro_socio],
            [titulo_depart],
            [titulo_locali]
        ], colWidths=[210])

        text_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))

        # Añadir la imagen con alineación a la derecha
        imagen = Image(imagen_path, width=60, height=60)

        # Crear la fila para la tabla principal
        row = [text_table, imagen]
        data.append(row)

    # Estilo de la tabla principal
    table_style = TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'), #image
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])

    # Crear la tabla principal
    table = Table(data, colWidths=[500, -250])
    table.setStyle(table_style)
    elements.append(table)

    # Construir el PDF
    doc.build(elements)
    return 'Informe de carnés PDF generado correctamente.'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, pass) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            flash('User created successfully')
            return redirect(url_for('login'))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash('Username already exists')
        finally:
            cursor.close()
    
    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, pass FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# Protect routes
@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'serve_image', 'uploaded_file']
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
