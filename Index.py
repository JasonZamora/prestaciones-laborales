from flask import Flask, render_template,request
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


app = Flask(__name__)


@app.route('/')
def home():
    return render_template('Prestaciones.html')


@app.route('/calcular_prestacion', methods=['POST'])
def calcular_aguinaldo():
    if request.method == 'POST':
        nombre = request.form['nombre']
        empresa = request.form['empresa']
        fecha_inicio = request.form['fecha_inicio']
        ingreso_sueldo = request.form['opcion']

        

        #TIPO DE CALCULO
        prestacion_calcular = request.form.get('prestacion')
        fecha_terminacion = request.form['fecha_terminacion']

        salario_promedio = 0.00
        salario_promedio_6 = 0.00
        dias_laborados = calcular_dias(fecha_inicio, fecha_terminacion)
        dias_total_laborados=dias_laborados

        prestacion = 0.0
        datos = {'nombreApellido':nombre, 'fechaFin':fecha_terminacion,'nombreEmpresa':empresa, 'fechaInicio':fecha_inicio, 'diasLaborados':dias_total_laborados, 'tipoPrestacion':prestacion_calcular}
        #---------------------------------------------
        #INGRESO DE SUELDO       
        #---------------------------------------------
        #_____Ingreso sueldo Simplificado_____
        if ingreso_sueldo == "Simplificado":
            salario_actual = float(request.form['salario_Actual'])
            aumento_toggle = request.form.get('aumento_toggle') == 'on'
                
            if aumento_toggle:               
                salario_anterior = float(request.form['aumento_monto'])
                aumento_fecha = request.form['aumento_fecha']
               
                meses_sueldo_aumento = int(calcular_dias(aumento_fecha, fecha_terminacion) / 30)
                meses_sueldo_anterior = 12 - meses_sueldo_aumento
                salario_promedio = ((salario_actual * meses_sueldo_aumento) + (salario_anterior * meses_sueldo_anterior)) / 12


                if (calcular_dias(aumento_fecha,fecha_terminacion) <= 183):
                    meses_sueldo_aumento_6 = int(calcular_dias(aumento_fecha, fecha_terminacion) / 30)
                    meses_sueldo_anterior_6 = 6 - meses_sueldo_aumento                   
                    salario_promedio_6 = ((salario_actual * meses_sueldo_aumento_6) + (salario_anterior * meses_sueldo_anterior_6)) / 6
                else:
                    salario_promedio_6 = (salario_actual*6)/6
            else:
                salario_promedio = (salario_actual*12)/12
                salario_promedio_6 = (salario_actual*6)/6

        #_____Ingreso sueldo Manual_____
        else:
            salarios = {}
            for i in range(1, 13):
                nombre_campo = 'S{}'.format(i)
                salario = request.form.get(nombre_campo)  
                if salario == '' or salario is None:  
                    salario = 0.00  # Establecer el salario en 0.00 si no se proporciona ningún valor
                else:
                    salario = float(salario)
                salarios[nombre_campo] = salario  
            
            # Convierte el diccionario en una lista de valores
            lista_salarios = [salarios.get('S{}'.format(i), 0.00) for i in range(1, 13)]
            salario_actual = lista_salarios[0]
            salario_promedio = sum(float(salario) for salario in lista_salarios)
            meses_nulos= lista_salarios.count(0.00)
            salario_promedio /= (12-meses_nulos) #saber cuantos meses no se toman en cuenta para el promedio
            
            salario_promedio_6 = sum(float(salario) for salario in lista_salarios[-6:]) / 6
            
                     
           
        #---------------------------------------------
        #TIPO DE CALCULO      
        #---------------------------------------------
        if prestacion_calcular == "Bono 14":
            prestacion=str(round(bono14_calculate(salario_promedio,fecha_terminacion,dias_laborados),2))
            datos['bono14']=prestacion

        if prestacion_calcular == "Aguinaldo":
            prestacion=str(round(aguinaldo_calculate(salario_promedio,fecha_terminacion,dias_laborados),2))
            datos['aguinaldo']=prestacion

        if prestacion_calcular == "Vacaciones":             
            prestacion=str(round(vacaciones_calculate(salario_promedio, fecha_terminacion,dias_laborados),2)) 
            datos['vacaciones']=prestacion          
 
        if (prestacion_calcular == "Indemnización" or prestacion_calcular == "Todo"):
            #primero se calcula las otras prestaciones para sumarselas a la indemnización
            bono14_value = bono14_calculate(salario_promedio,fecha_terminacion,dias_laborados)
            Agunaldo_value = aguinaldo_calculate(salario_promedio,fecha_terminacion,dias_laborados)
            vacaciones_value = vacaciones_calculate(salario_promedio, fecha_terminacion,dias_laborados)           
            Indemnizacion_value = indemnizacion_calculate(salario_promedio_6, dias_total_laborados)

            #luego se suma el total que va a recibir
            prestacion = round(Indemnizacion_value + bono14_value + Agunaldo_value + vacaciones_value, 2)

            #asignar valores
            if prestacion_calcular == "Indemnización":
                datos['tiempo']=Indemnizacion_value
                datos['indemnizacion']=prestacion
            else:
                datos['bono14']=bono14_value
                datos['aguinaldo']=Agunaldo_value
                datos['vacaciones']=vacaciones_value
                datos['tiempo']=Indemnizacion_value
                datos['indemnizacion']=prestacion
    
    
    datos['salarioPromedio']=Decimal(salario_promedio).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    datos['salario']=Decimal(salario_actual).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    
    return render_template('Resultados.html',aguinaldo=prestacion, resultados=datos)




#***************************calculos********************************************************
def bono14_calculate(salario_promedio, fecha_terminacion, dias_laborados):
    prestacion =0.00

    if dias_laborados > 365:
        yearNow = datetime.now().year
        fecha_inicio_B14 = datetime(yearNow - 1, 7, 1)    
        fecha_inicio_B14 = fecha_inicio_B14.strftime('%Y-%m-%d') 
        dias_laborados= calcular_dias(fecha_inicio_B14, fecha_terminacion)
        
        if dias_laborados > 365:
            yearNow = datetime.now().year
            fecha_inicio_B14 = datetime(yearNow , 7, 1)    
            fecha_inicio_B14 = fecha_inicio_B14.strftime('%Y-%m-%d') 
            dias_laborados= calcular_dias(fecha_inicio_B14, fecha_terminacion)

    
    prestacion = Decimal(salario_promedio / 365 * dias_laborados).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    return prestacion


def aguinaldo_calculate(salario_promedio, fecha_terminacion,dias_laborados):
    if dias_laborados > 365:                    
        yearNow = datetime.now().year
        fecha_inicio_Aguinaldo = datetime(yearNow - 1, 12, 1)              
        fecha_inicio_Aguinaldo = fecha_inicio_Aguinaldo.strftime('%Y-%m-%d') 
        dias_laborados = calcular_dias(fecha_inicio_Aguinaldo, fecha_terminacion)

        if dias_laborados > 365:
            yearNow = datetime.now().year
            fecha_inicio_ag = datetime(yearNow , 12, 1)    
            fecha_inicio_ag = fecha_inicio_ag.strftime('%Y-%m-%d') 
            dias_laborados= calcular_dias(fecha_inicio_ag, fecha_terminacion)

    prestacion = Decimal(salario_promedio / 365 * dias_laborados).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)

    return prestacion

def vacaciones_calculate(salario_promedio, fecha_terminacion,dias_laborados): 
    if dias_laborados > 365:  
        yearNow = datetime.now().year                  
        fecha_inicio_vacaciones= datetime(yearNow, 1, 1)              
        fecha_inicio_vacaciones = fecha_inicio_vacaciones.strftime('%Y-%m-%d')   
        dias_laborados = calcular_dias(fecha_inicio_vacaciones, fecha_terminacion)                
        dias_vacaciones = int(request.form.get('dias_vacaciones', 0)) 
        
        if dias_laborados > 365:
            fecha_fin = datetime.strptime(fecha_terminacion, '%Y-%m-%d')
            year = fecha_fin.year
            fecha_inicio_vacaciones_2 = datetime(year, 1, 1)  
            fecha_inicio_vacaciones_2 = fecha_inicio_vacaciones_2.strftime('%Y-%m-%d')   
            dias_laborados = calcular_dias(fecha_inicio_vacaciones_2, fecha_terminacion)
        
    prestacion= Decimal(((salario_promedio/365)*(dias_vacaciones/30))*dias_laborados).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    return prestacion    

def indemnizacion_calculate(salario_promedio_6, dias_total_laborados):
    prestacion =Decimal((salario_promedio_6/365) * dias_total_laborados).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    return    prestacion

def calcular_dias(fecha_inicio,fecha_fin):
    fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    dias_laborados= (fecha_fin-fecha_inicio).days
    return dias_laborados


if __name__ =='__main__':
    app.run(debug=True)