"""
/***************************************************************************
 Compiler
                                 A QGIS plugin
 Собирает слои для АРМ
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-06-22
        copyright            : (C) 2021 by Travin Alexzander/Roslesinforg
        email                : travin1995@inbox.ru
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox
import processing
import os
from qgis.core import (QgsApplication,
                       QgsProject,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsField,
                       QgsFields,
                       QgsFeature,
                       QgsVectorDataProvider,
                       QgsVectorLayer,
                       QgsVectorFileWriter,
                       QgsWkbTypes,
                       QgsVectorLayerUtils,
                       QgsMapLayerType,
                       QgsMapLayer,
                       )

from .resources import *
from .ARM_compiler_dialog import CompilerDialog


class Compiler:

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        self.actions = []
        self.menu = self.tr(u'&ARM compiler')

        self.first_start = None

    def tr(self, message):
        return QCoreApplication.translate('Compiler', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        icon_path = ':/plugins/ARM_compiler/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'ARM compiler'),
            callback=self.run,
            parent=self.iface.mainWindow())

        self.first_start = True

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&ARM compiler'),
                action)
            self.iface.removeToolBarIcon(action)

    # Растановка ID линейным объектам
    def cipher(self, layer):
        ciper = {'ГИДР': 27, 'РУЧЬИ': 28, 'РУЧЕЙ': 28, 'КАНАЛ': 29, 'ЖЕЛЕЗН': 30, 'ЖД': 30, 'АВТО': 31, 'ГРУНТ': 31,
                 'ЗИМНИК': 32, 'ТРОПА': 33, 'ТРОПЫ': 33, 'ЛЕСН': 33, 'ЛЕСОВ': 33, 'КАНАВ': 34, 'ГРАНИЦ': 35,
                 'ПРОСЕК': 36, 'ЛЭП': 45, 'ГАЗ': 46, 'ТЕЛЕФОН': 47, 'ЛИНИЯ': 47, 'СВЯЗЬ': 47, 'СВЯЗИ': 47,
                 'МЕЛИОРАЦ': 48, 'ПОЖАР': 49, 'ПРОЧИЕ': 50, 'ВОДОПРОВОД': 56, 'НЕФТ': 82}
        if layer.type() == 0:
            if layer.wkbType() == 5:
                layer.dataProvider().addAttributes([QgsField("LineID", QVariant.Int)])
                layer.updateFields()
            else:
                pass
            for i in ciper.keys():
                if i in layer.name().upper():
                    ilist = []
                    ilist.append(ciper[i])
                    layer.startEditing()
                    for feature in layer.getFeatures():
                        findx = layer.dataProvider().fieldNameIndex("LineID")
                        layer.dataProvider().changeAttributeValues(
                            {feature.id(): {findx: int(ilist[0])}})
                    layer.commitChanges()

    # Сохранение слоёв в ESRI Shapefile с СК
    def saveSHP(self, catalog, CRS, crsname, layer):
        cs = QgsCoordinateTransform(layer.crs(),
                                    CRS, QgsProject.instance())
        if layer.type() == 0:
            error = QgsVectorFileWriter.writeAsVectorFormat(layer,
                                                            catalog + f"/{crsname}_" + layer.name(),
                                                            'utf-8',
                                                            cs,
                                                            "ESRI Shapefile")
            if error[0] == QgsVectorFileWriter.NoError:
                pass
        else:
            pass

    # Удаление слоёв MIF открытие сохранёных SHP файлов
    def remove(self, catalog, crsname, layer):
        if layer.type() == 0:
            QgsProject.instance().addMapLayer(
                QgsVectorLayer(f"{catalog}/{crsname}_{layer.name()}.shp", f"{crsname}_{layer.name()}",
                               "ogr"))
            QgsProject.instance().removeMapLayer(layer)
        else:
            pass

    # Выбор каталога сохранения
    def dct(self):
        self.dlg.lineEdit.setText(QFileDialog.getExistingDirectory())

    # Создание полигонов кварталов в СК
    def polkw(self, catalog, selectedLayerName, crsname, layer):
        if layer.name() == f"{crsname}_{selectedLayerName}":
            processing.run(
                "native:dissolve",
                {'INPUT': layer,
                 'FIELD': self.dlg.comboBox2.currentText(),
                 'OUTPUT': f"{catalog}/{crsname}_полигоны-квартала.shp"})
            QgsProject.instance().addMapLayer(
                QgsVectorLayer(f"{catalog}/{crsname}_полигоны-квартала.shp", f"{crsname}_полигоны-квартала",
                               "ogr"))

    # Объединение линейных слоёв в один
    def uline(self, catalog, crsname):
        inputlayer = []
        for layer in QgsProject.instance().layerTreeRoot().children():
            if layer.layer().type() == 0:
                if layer.layer().wkbType() == 5:
                    inputlayer.append(layer.layer())
        processing.runAndLoadResults("qgis:mergevectorlayers",
                                     {'LAYERS': inputlayer, 'OUTPUT': f'{catalog}/{crsname}_LINES.shp'})

    # Разбитие линейного слоя по атрибуту
    def split(self, CRS, crsname, catalog):
        key = ['Гидрография', 'Ручей', 'Каналы', 'ЖД', 'Дороги', 'Зимник', 'Лесные_дор', 'Канавы', 'Границы', 'Просека',
               'ЛЭП', 'ГАЗ', 'Линия_связи', 'Мелиорация', 'Пр-пожарные', 'Прочие_трассы', 'Водопровод', 'Нефтепровод']
        vlaue = [27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 45, 46, 47, 48, 49, 50, 56, 82]
        layers = self.iface.mapCanvas().layers()
        selectedLayer = layers[self.dlg.comboBox_i.currentIndex()]
        if selectedLayer.wkbType() == 5:
            selectedfield = self.dlg.comboBox2_i.currentText()
            findx = selectedLayer.dataProvider().fieldNameIndex(f"{selectedfield}")
            lst = []
            for feature in selectedLayer.getFeatures():
                lst.append(feature.attributes()[findx])
            processing.run("qgis:splitvectorlayer",
                           {'INPUT': selectedLayer,
                            'FIELD': f'{selectedfield}',
                            'FILE_TYPE': 0,
                            'OUTPUT': f'{catalog}'})
            for vl in list(set(lst)):
                if vl in vlaue:
                    gpkglayer = QgsVectorLayer(f"{catalog}/{selectedfield}_{vl}.gpkg", f"{key[vlaue.index(vl)]}",
                                               "ogr")
                    QgsProject.instance().addMapLayer(gpkglayer)
                    layers.append(gpkglayer)
            for layer in layers:
                if layer.type() == 0:
                    self.saveSHP(catalog, CRS, crsname, layer)
                    vlayer = QgsVectorLayer(f"{catalog}/{crsname}_{layer.name()}.shp", f"{crsname}_{layer.name()}",
                                            "ogr")
                    QgsProject.instance().addMapLayer(vlayer)
                    QgsProject.instance().removeMapLayer(layer)
                else:
                    pass
            self.dlg.close()
            self.message(catalog)
        else:
            error = QMessageBox()
            error.setWindowTitle("Ошибка!")
            error.setText(
                "Выбранный слой не линейный!")
            error.exec_()

    # Выбор поля "Квартальности" пользователем
    def change_field(self, i):
        self.dlg.comboBox2.clear()
        layers = QgsProject.instance().layerTreeRoot().children()
        selectedLayer = layers[i].layer()
        if selectedLayer.type() == QgsMapLayerType.VectorLayer:
            fieldnames = [field.name() for field in selectedLayer.fields()]
            self.dlg.comboBox2.addItems(fieldnames)
        else:
            pass

    # Выбор поля ID линейных пользователем
    def change_field_i(self, i):
        self.dlg.comboBox2_i.clear()
        layers = QgsProject.instance().layerTreeRoot().children()
        selectedLayer = layers[i].layer()
        if selectedLayer.type() == QgsMapLayerType.VectorLayer:
            fieldnames = [field.name() for field in selectedLayer.fields()]
            self.dlg.comboBox2_i.addItems(fieldnames)
        else:
            pass

    # Установка для слоёв MIF СК проекта
    def set_crs(self, layer):
        layer.setCrs(QgsProject.instance().crs())

    # Сообщение по завершении
    def message(self, catalog):
        msbox = QMessageBox()
        msbox.setIcon(QMessageBox.Information)
        msbox.setText(f"Результирующие слои сохранены: {catalog}")
        msbox.setWindowTitle("Готово!")
        msbox.exec()

    def apply(self):
        CRS = self.dlg.mQgsProjectionSelectionWidget.crs()
        crsname = format(CRS.description())
        crsname = crsname.replace(" ", "")
        crsname = crsname.replace("/", "-")
        selectedLayerIndex = self.dlg.comboBox.currentIndex()
        selectedLayer = self.iface.mapCanvas().layers()[selectedLayerIndex]
        selectedLayerName = selectedLayer.name()
        catalog = self.dlg.lineEdit.text()
        if catalog == '':
            error_msg = QMessageBox()
            error_msg.setWindowTitle("Ошибка!")
            error_msg.setText(
                "Папка назначения не задана!")
            error_msg.exec_()
        elif self.dlg.tabWidget.currentIndex() == 0:
            if selectedLayer.wkbType() == 3 or selectedLayer.wkbType() == 6:
                for layer in self.iface.mapCanvas().layers():
                    if layer.type() == QgsMapLayer.VectorLayer:
                        self.set_crs(layer)
                        self.saveSHP(catalog, CRS, crsname, layer)
                        self.remove(catalog, crsname, layer)
                    else:
                        pass
                layers = QgsProject.instance().mapLayers().values()
                for layer in layers:
                    self.polkw(catalog, selectedLayerName, crsname, layer)
                    self.cipher(layer)
                self.uline(catalog, crsname)
                self.message(catalog)
                self.dlg.close()
            else:
                error_msg_2 = QMessageBox()
                error_msg_2.setWindowTitle("Ошибка!")
                error_msg_2.setText(
                    "Выбранный слой не полигональный!")
                error_msg_2.exec_()
        elif self.dlg.tabWidget.currentIndex() == 1:
            self.split(CRS, crsname, catalog)
        else:
            pass

    def cancel(self):
        self.dlg.close()

    def run(self):
        self.dlg = CompilerDialog()
        self.dlg.toolButton.clicked.connect(self.dct)
        self.dlg.lineEdit.clear()
        self.dlg.comboBox.clear()
        self.dlg.comboBox2.clear()
        self.dlg.comboBox_i.clear()
        self.dlg.comboBox2_i.clear()
        self.dlg.OK.clicked.connect(self.apply)
        self.dlg.Cancel.clicked.connect(self.cancel)
        lst = []
        for layer in self.iface.mapCanvas().layers():
            if layer.type() == QgsMapLayerType.VectorLayer:
                lst.append(layer.type())
                self.dlg.comboBox.addItems([layer.name()])
                self.dlg.comboBox_i.addItems([layer.name()])
                self.dlg.comboBox.setCurrentIndex(0)
                self.dlg.comboBox.currentIndexChanged.connect(self.change_field)
                self.change_field(0)
                self.dlg.comboBox_i.setCurrentIndex(0)
                self.dlg.comboBox_i.currentIndexChanged.connect(self.change_field_i)
                self.change_field_i(0)
                self.dlg.mQgsProjectionSelectionWidget.setCrs(QgsProject.instance().crs())
                self.dlg.tabWidget.setCurrentIndex(0)
                self.dlg.show()
            if layer.type() == QgsMapLayerType.RasterLayer:
                QgsProject.instance().removeMapLayer(layer)
            else:
                pass
        if QgsMapLayerType.VectorLayer not in lst:
            error = QMessageBox()
            error.setWindowTitle("Ошибка!")
            error.setText('Проект не содержит векторных слоёв!\n'
                          "Добавьте слои в проект!")
            error.exec_()
            
