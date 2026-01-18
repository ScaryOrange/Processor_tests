import os
from qgis.core import (
    QgsVectorLayer, QgsProject, QgsFeatureRequest,
    QgsFields, QgsField, QgsCoordinateReferenceSystem,
    QgsFeature, QgsCoordinateTransform
)
from qgis.PyQt.QtCore import QVariant


class Processor:
    def __init__(self):
        self.project = QgsProject.instance()

    def load_layer(self, file_path):
        """Загружает векторный слой из GeoJSON"""

        layer = QgsVectorLayer(file_path, "cities", "ogr")
        if not layer.isValid():
            raise ValueError("Не удалось загрузить слой")

        self.project.addMapLayer(layer)
        self.project.addMapLayer(layer)
        return layer

    def filter_features(self, layer, expression):
        """Фильтрует объекты по выражению"""
        request = QgsFeatureRequest()
        request.setFilterExpression(expression)
        features = [f for f in layer.getFeatures(request)]
        return features

    def to_gsk_2011(self, layer, epsg='EPSG:7683'):
        """Перевод в систему координат ГСК-2011"""
        source_crs = QgsCoordinateReferenceSystem(layer.crs().authid())
        new_crs = QgsCoordinateReferenceSystem(epsg)
        trans = QgsCoordinateTransform(source_crs, new_crs, self.project)

        transformed_layer = QgsVectorLayer(
            f"Polygon?crs={epsg}",
            f"{layer.name()}_transformed",
            "memory"
        )

        transformed_layer.dataProvider().addAttributes(layer.fields())
        transformed_layer.updateFields()

        features = []
        for feature in layer.getFeatures():
            new_feature = QgsFeature(feature.fields())
            geom = feature.geometry()
            if not geom.isEmpty():
                geom.transform(trans)
                new_feature.setGeometry(geom)
            features.append(new_feature)

        transformed_layer.dataProvider().addFeatures(features)

        return transformed_layer

    def create_buffer_layer(self, input_layer, distance):
        """Создает буферный слой"""
        fields = QgsFields()
        fields.append(QgsField("population", QVariant.Int))

        buffer_layer = QgsVectorLayer(
            f"Polygon?crs={'EPSG:4326'}",
            "buffered_cities",
            "memory"
        )

        buffer_layer.dataProvider().addAttributes(fields)
        buffer_layer.updateFields()

        features = []
        for feature in input_layer:
            # вместо feature.clone() (предполгаю, что ожидалось копирование значения полей)
            # используется конструктор QgsFeature()
            new_feature = QgsFeature(buffer_layer.fields())
            new_feature['population'] = feature['population'] * 2
            geom = feature.geometry().buffer(distance, 25)
            new_feature.setGeometry(geom)
            features.append(new_feature)

        buffer_layer.dataProvider().addFeatures(features)
        self.project.addMapLayer(buffer_layer)
        return buffer_layer

    def full_pipeline(self, file_path):
        """Полный пайплайн обработки"""
        layer = self.load_layer(file_path)
        filtered = self.filter_features(layer, "population >= 1000")
        buffer_layer = self.create_buffer_layer(filtered, 1000)
        return buffer_layer


if __name__ == "__main__":
    processor = Processor()
    layer = processor.load_layer("test_data.geojson")
    # было population >= 1000
    filtered = processor.filter_features(layer, "population > 1000")
    print(f"Отфильтровано объектов: {len(filtered)}")
    buffer_layer = processor.create_buffer_layer(filtered, 1000)
