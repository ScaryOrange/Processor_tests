import pytest
import sys
from pathlib import Path
from qgis.core import QgsVectorLayer, QgsWkbTypes, QgsProject

sys.path.insert(0, str(Path(__file__).parent.parent))
from processor import Processor


@pytest.fixture
def processor():
    """Фикстура для процессора"""
    return Processor()


@pytest.fixture
def test_file_path():
    """Фикстура для пути к файлу"""
    path = Path(__file__).parent.parent / 'test_data.geojson'
    if not path.exists():
        pytest.skip(f"Файл не найден: {path}")
    return str(path)


@pytest.fixture
def loaded_layer(processor, test_file_path):
    """Фикстура для слоя"""
    layer = processor.load_layer(test_file_path)
    if not layer or not layer.isValid():
        pytest.fail("Не удалось загрузить слой")
    return layer


@pytest.fixture
def loaded_filter_features(loaded_layer, processor):
    """Фикстура отфильтрованых объектов"""
    return processor.filter_features(loaded_layer, "population > 1000")


@pytest.fixture
def load_buffer_layer(loaded_filter_features, processor):
    """Фикстура буферного слоя"""
    buffer = processor.create_buffer_layer(loaded_filter_features, 1000)
    return buffer


@pytest.fixture(autouse=True)
def cleanup_project():
    """Автоматическая очистка проекта между тестами"""
    yield
    project = QgsProject.instance()
    project.removeAllMapLayers()


def test_layer_basics(loaded_layer):
    """Тест слоя"""
    assert isinstance(loaded_layer, QgsVectorLayer)
    assert loaded_layer.isValid()
    assert loaded_layer.featureCount() == 7
    assert loaded_layer.crs().postgisSrid() == 4326


def test_filter_features_population(loaded_filter_features):
    """Тест отфильтрованных объектов """
    assert len(loaded_filter_features) == 3
    assert loaded_filter_features[0]['population'] == 2500


def test_create_buffer_layer(load_buffer_layer):
    """Тест создания буферного слоя"""
    assert load_buffer_layer.isValid() is True
    assert load_buffer_layer.geometryType() == QgsWkbTypes.PolygonGeometry
    assert len(load_buffer_layer) == 3


def test_full_pipeline(processor, test_file_path):
    """Тест полного паплайна обработки"""
    processor.full_pipeline(test_file_path)
    assert processor.project.mapLayersByName('buffered_cities')


def test_to_gsk_2011(loaded_layer, processor):
    """Тест перевода в ГСК-2011"""
    assert processor.to_gsk_2011(loaded_layer).crs().postgisSrid() == 7683
    assert processor.to_gsk_2011(loaded_layer, 'epsg:1234').crs().postgisSrid() == 0
