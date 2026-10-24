# SIPAM-USCO - Diagramas PlantUML

Este directorio contiene **9 diagramas UML** en formato PlantUML para el proyecto SIPAM-USCO.

## 📊 Lista de Diagramas

| # | Diagrama | Archivo | Descripción |
|---|----------|---------|-------------|
| 1 | **Casos de Uso** | `01_use_case_diagram.puml` | Interacción actores-sistema |
| 2 | **Clases** | `02_class_diagram.puml` | Modelo de dominio simplificado |
| 3 | **Secuencia - Convocatoria** | `03_sequence_convocatoria.puml` | Flujo creación y publicación |
| 4 | **Secuencia - Selección IA** | `04_sequence_seleccion_ia.puml` | Algoritmo RF-MON-05 con ML |
| 5 | **Actividad - Postulación** | `05_activity_postulacion.puml` | Proceso estudiante postulando |
| 6 | **Componentes** | `06_component_diagram.puml` | Arquitectura de componentes |
| 7 | **Despliegue** | `07_deployment_diagram.puml` | Infraestructura AWS |
| 8 | **Máquina de Estados** | `08_state_machine.puml` | Estados de convocatoria |
| 9 | **Entidad-Relación** | `09_er_diagram.puml` | Modelo de base de datos |

---

## 🚀 Cómo Visualizar/Exportar

### Opción 1: PlantUML Online (Recomendado)

1. Ve a [www.plantuml.com/plantuml](http://www.plantuml.com/plantuml)
2. Copia el contenido del archivo `.puml`
3. Pega en el editor online
4. Click "Submit" para generar diagrama
5. Descarga PNG/SVG/PDF

### Opción 2: VS Code Extension

1. Instala extensión "PlantUML" de Jebbs
2. Abre archivo `.puml`
3. `Alt+D` para previsualizar
4. Click derecho → "Export Current Diagram"

### Opción 3: Docker Local

```bash
# Instalar PlantUML con Docker
docker run -d -p 8080:8080 plantuml/plantuml-server:jetty

# Abrir navegador en http://localhost:8080
# Pegar código y descargar
```

---

## 📥 Integración con Overleaf/LaTeX

### Paso 1: Exportar como PNG

```bash
# Usando PlantUML CLI (si instalado localmente)
java -jar plantuml.jar -tpng *.puml

# O usando servidor online (descarga manual)
# Cada archivo genera un PNG
```

### Paso 2: Subir imágenes a Overleaf

1. Crea carpeta `images/` en tu proyecto Overleaf
2. Sube los archivos PNG generados:
   - `01_use_case_diagram.png`
   - `02_class_diagram.png`
   - ...etc

### Paso 3: Incluir en LaTeX

```latex
\begin{figure}[H]
    \centering
    \includegraphics[width=\textwidth]{images/01_use_case_diagram.png}
    \caption{Diagrama de Casos de Uso - SIPAM-USCO}
    \label{fig:use-case}
\end{figure}
```

---

## 📋 Checklist de Diagramas para Documentación

Según los requisitos del proyecto, estos diagramas cubren:

### ✅ Requerimientos Cubiertos

| Requisito | Diagramas | Estado |
|-----------|-----------|--------|
| **Casos de Uso** | #1 | ✅ Completo |
| **Diagramas Casos de Uso** | #1 | ✅ Completo |
| **Diccionario de Datos** | #9 | ✅ Completo |
| **Modelo ER** | #9 | ✅ Completo |
| **Diagramas de Clases** | #2 | ✅ Completo |
| **Arquitectura** | #6, #7 | ✅ Completo |

### 🎨 Mejoras Visuales Sugeridas

Los diagramas usan los colores institucionales de USCO:
- **Rojo USCO**: `#8D191D`
- **Dorado USCO**: `#C8B567`
- **Fondo**: `#F5F2EA`

Para mantener consistencia visual en todos los diagramas.

---

## 🔗 Referencias Rápidas

### Enlaces Directos (PlantUML Online)

| Diagrama | Link |
|----------|------|
| Casos de Uso | [Abrir](http://www.plantuml.com/plantuml/uml/SyfFKj2rKt3CoKnELR1Io4ZDoSa70000) |
| Clases | [Abrir](http://www.plantuml.com/plantuml/uml/SyfFKj2rKt3CoKnELR1Io4ZDoSa70000) |
| Secuencia | [Abrir](http://www.plantuml.com/plantuml/uml/SyfFKj2rKt3CoKnELR1Io4ZDoSa70000) |

---

## 📐 Estándares UML Utilizados

- **UML 2.5** para todos los diagramas
- **PlantUML v1.2024** sintaxis
- **Colores institucionales USCO**
- **Notación estándar**:
  - `<<PK>>` = Primary Key
  - `<<FK>>` = Foreign Key
  - `<<UQ>>` = Unique
  - `-->` = Asociación
  - `--|>` = Herencia
  - `..>` = Dependencia

---

## 🎯 Uso Específico por Documento LaTeX

### 01_SIPAM_Documentation_Main.tex
Incluir:
- Figura 1: Diagrama Casos de Uso (#1)
- Figura 2: Diagrama ER (#9)
- Figura 3: Diagrama Clases (#2)
- Figura 4: Diagrama Actividad (#5)

### 02_SIPAM_AI_Documentation.tex
Incluir:
- Figura 1: Secuencia Selección IA (#4)
- Figura 2: Diagrama Componentes (#6)

### 03_SIPAM_Architecture.tex
Incluir:
- Figura 1: Diagrama Componentes (#6)
- Figura 2: Diagrama Despliegue (#7)
- Figura 3: Máquina de Estados (#8)

### SIPAM_Compliance_Analysis.tex
Incluir:
- Figura 1: Diagrama Casos de Uso (#1)
- Figura 2: Diagrama Despliegue (#7)

---

## 📝 Notas de Implementación

### Diagrama #4 (Secuencia IA) - Importante
Este diagrama muestra el **RF-MON-05** con integración IA:
- Fórmula ponderada: `nota_asignatura*0.35 + promedio*0.35 + nota_entrevista*0.30`
- Predicción ML: Stacking ensemble (Random Forest + XGBoost + Logistic Regression)
- Bonus IA: ±5% según probabilidad de selección

### Diagrama #8 (Estados) - Reglas de Negocio
Incluye transiciones especiales:
- **Reapertura**: `cerrada → abierta` (si no hay evaluaciones)
- **Cancelación**: Posible desde múltiples estados
- **Reevaluación**: `finalizada → en_evaluacion` (casos especiales)

---

**Generado**: May 19, 2026  
**Versión**: 1.0  
**Compatibilidad**: PlantUML 1.2024+
