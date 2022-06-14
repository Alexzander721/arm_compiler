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
        self.instance = QgsProject.instance()
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

    def cipher(self, layer):
        """
        Растановка ID линейным объектам
        """
        if self.dlg.checkBox.isChecked():
            ciper = {'ГИДР': 27, 'РУЧЬИ': 28, 'РУЧЕЙ': 28, 'КАНАЛ': 29, 'ЖЕЛЕЗН': 30, 'ЖД': 30, 'АВТО': 31, 'ГРУНТ': 31,
                     'ЗИМНИК': 32, 'ТРОПА': 33, 'ТРОПЫ': 33, 'ЛЕСН': 33, 'ЛЕСОВ': 33, 'КАНАВ': 34, 'ГРАНИЦ': 35,
                     'ПРОСЕК': 36, 'ЛЭП': 45, 'ГАЗ': 46, 'ТЕЛЕФОН': 47, 'ЛИНИЯ': 47, 'СВЯЗЬ': 47, 'СВЯЗИ': 47,
                     'МЕЛИОРАЦ': 48, 'ПОЖАР': 49, 'ПРОЧИЕ': 50, 'ВОДОПРОВОД': 56, 'НЕФТ': 82}
        else:
            ciper = {'ГИДР': 52, 'РУЧЬИ': 54, 'РУЧЕЙ': 54, 'КАНАЛ': 54, 'ЖЕЛЕЗН': 55, 'ЖД': 55, 'АВТО': 57, 'ГРУНТ': 58,
                     'ЗИМНИК': 66, 'ТРОПА': 66, 'ТРОПЫ': 66, 'ЛЕСН': 66, 'ЛЕСОВ': 64, 'КАНАВ': 54, 'ЛЭП': 73,
                     'ТЕЛЕФОН': 71, 'ЛИНИЯ': 71, 'СВЯЗЬ': 71, 'СВЯЗИ': 71, 'ПРОЧИЕ': 59}
        if layer.type() == 0:
            if layer.wkbType() == 5:
                layer.dataProvider().addAttributes([QgsField("LineID", QVariant.Int)]), layer.updateFields()
            for i in ciper.keys():
                if i in layer.name().upper():
                    ilist = [ciper[i]]
                    layer.startEditing()
                    for feature in layer.getFeatures():
                        layer.dataProvider().changeAttributeValues(
                            {feature.id(): {layer.dataProvider().fieldNameIndex("LineID"): int(ilist[0])}})
                    layer.commitChanges()

    def saveSHP(self, catalog, CRS, crsname, layer):
        """
        Сохранение слоёв в ESRI Shapefile с СК
        """
        cs = QgsCoordinateTransform(layer.crs(),
                                    CRS, self.instance)
        if layer.type() == 0:
            error = QgsVectorFileWriter.writeAsVectorFormat(layer,
                                                            catalog + f"/{crsname}_" + layer.name(),
                                                            'utf-8',
                                                            cs,
                                                            "ESRI Shapefile")
            if error[0] == QgsVectorFileWriter.NoError:
                pass

    def remove(self, catalog, crsname, layer):
        """
        Удаление слоёв MIF открытие сохранёных SHP файлов
        """
        if layer.type() == 0:
            self.instance.addMapLayer(
                QgsVectorLayer(f"{catalog}/{crsname}_{layer.name()}.shp", f"{crsname}_{layer.name()}",
                               "ogr"))
            self.instance.removeMapLayer(layer)

    def dct(self):
        """
        Выбор каталога сохранения
        """
        self.dlg.lineEdit.setText(QFileDialog.getExistingDirectory())

    def polkw(self, catalog, slayername, crsname, layer):
        """
        Создание полигонов кварталов в СК
        """
        if layer.name() == f"{crsname}_{slayername}":
            processing.run(
                "native:dissolve",
                {'INPUT': layer,
                 'FIELD': self.dlg.comboBox2.currentText(),
                 'OUTPUT': f"{catalog}/{crsname}_полигоны-квартала.shp"})
            self.instance.addMapLayer(
                QgsVectorLayer(f"{catalog}/{crsname}_полигоны-квартала.shp", f"{crsname}_полигоны-квартала",
                               "ogr"))

    def uline(self, catalog, crsname):
        """
        Объединение линейных слоёв в один
        """
        inputlayer = []
        for layer in self.instance.layerTreeRoot().children():
            if layer.layer().type() == 0:
                if layer.layer().wkbType() == 5:
                    inputlayer.append(layer.layer())
        processing.runAndLoadResults("qgis:mergevectorlayers",
                                     {'LAYERS': inputlayer, 'OUTPUT': f'{catalog}/{crsname}_LINES.shp'})

    def split(self, CRS, crsname, catalog):
        """
        Разбитие линейного слоя по атрибуту
        """
        if self.dlg.checkBox.isChecked():
            key = ['Гидрография', 'Ручей', 'Каналы', 'ЖД', 'Дороги', 'Зимник', 'Лесные_дор', 'Канавы', 'Границы',
                   'Просека', 'ЛЭП', 'ГАЗ', 'Линия_связи', 'Мелиорация', 'Пр-пожарные', 'Прочие_трассы', 'Водопровод',
                   'Нефтепровод']
            vlaue = [27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 45, 46, 47, 48, 49, 50, 56, 82]
        else:
            key = ['Гидрография', 'Ручей', 'Каналы', 'ЖД', 'Дороги', 'Дороги_грунт', 'Зимник', 'Лесные_дор', 'Канавы',
                   'ЛЭП', 'Прочие', 'Линия_связи']
            vlaue = [52, 54, 54, 55, 57, 58, 66, 66, 54, 73, 59, 71]
        layers = self.iface.mapCanvas().layers()
        slayer = self.dlg.comboBox_i.itemData(self.dlg.comboBox_i.currentIndex())
        if slayer.wkbType() == 5:
            selectedfield = self.dlg.comboBox2_i.currentText()
            findx = slayer.dataProvider().fieldNameIndex(f"{selectedfield}")
            lst = []
            [lst.append(feature.attributes()[findx]) for feature in slayer.getFeatures()]
            processing.run("qgis:splitvectorlayer",
                           {'INPUT': slayer,
                            'FIELD': f'{selectedfield}',
                            'FILE_TYPE': 0,
                            'OUTPUT': f'{catalog}'})
            for vl in list(set(lst)):
                if vl in vlaue:
                    gpkglayer = QgsVectorLayer(f"{catalog}/{selectedfield}_{vl}.gpkg", f"{key[vlaue.index(vl)]}",
                                               "ogr")
                    self.instance.addMapLayer(gpkglayer)
                    layers.append(gpkglayer)
            for layer in layers:
                if layer.type() == 0:
                    self.saveSHP(catalog, CRS, crsname, layer)
                    vlayer = QgsVectorLayer(f"{catalog}/{crsname}_{layer.name()}.shp", f"{crsname}_{layer.name()}",
                                            "ogr")
                    self.instance.addMapLayer(vlayer)
                    self.instance.removeMapLayer(layer)
            self.dlg.close()
            self.message(catalog)
        else:
            error = QMessageBox()
            error.setWindowTitle("Ошибка!")
            error.setText(
                "Выбранный слой не линейный!")
            error.exec_()

    def set_crs(self, layer):
        """
        Установка для слоёв MIF СК проекта
        """
        layer.setCrs(self.instance.crs())

    def message(self, catalog):
        """
        Сообщение по завершении
        """
        msbox = QMessageBox()
        msbox.setIcon(QMessageBox.Information)
        msbox.setText(f"Результирующие слои сохранены: {catalog}")
        msbox.setWindowTitle("Готово!")
        msbox.exec()

    def apply(self):
        """
        Запуск алгоритмов обработки, проверка на ошибки
        """
        CRS = self.dlg.mQgsProjectionSelectionWidget.crs()
        cname = format(CRS.description())
        cname = cname.replace(" ", "")
        cname = cname.replace("/", "-")
        slayer = self.dlg.comboBox.itemData(self.dlg.comboBox.currentIndex())
        slayername = slayer.name()
        catalog = self.dlg.lineEdit.text()
        if not bool(catalog):
            error_msg = QMessageBox()
            error_msg.setWindowTitle("Ошибка!")
            error_msg.setText(
                "Папка назначения не задана!")
            error_msg.exec_()
        elif self.dlg.tabWidget.currentIndex() == 0:
            if slayer.wkbType() == 3 or slayer.wkbType() == 6:
                for layer in self.iface.mapCanvas().layers():
                    if layer.type() == QgsMapLayer.VectorLayer:
                        self.set_crs(layer)
                        self.saveSHP(catalog, CRS, cname, layer)
                        self.remove(catalog, cname, layer)
                for layer in self.instance.mapLayers().values():
                    self.polkw(catalog, slayername, cname, layer)
                    self.cipher(layer)
                self.uline(catalog, cname)
                self.message(catalog)
                self.dlg.close()
            else:
                error_msg_2 = QMessageBox()
                error_msg_2.setWindowTitle("Ошибка!")
                error_msg_2.setText(
                    "Выбранный слой не полигональный!")
                error_msg_2.exec_()
        elif self.dlg.tabWidget.currentIndex() == 1:
            self.split(CRS, cname, catalog)

    def cancel(self):
        """
        Закрытие окна программы
        """
        self.dlg.close()

    def choice_layer(self):
        """
        Выбор слоя
        """
        self.dlg.comboBox.clear()
        self.dlg.comboBox_i.clear()
        for layer in self.instance.mapLayers().values():
            if layer.type() == QgsMapLayer.VectorLayer and layer.wkbType() == 3 or \
                    layer.type() == QgsMapLayer.VectorLayer and layer.wkbType() == 6:
                self.dlg.comboBox.addItem(layer.name(), layer)
                self.dlg.comboBox_i.addItem(layer.name(), layer)

    def choice_field(self):
        """
        Выбор поля "Квартальности" пользователем
        """
        self.dlg.comboBox2.clear()
        slayer = self.dlg.comboBox.itemData(self.dlg.comboBox.currentIndex())
        if slayer is not None:
            [self.dlg.comboBox2.addItem(field.name()) for field in slayer.fields()]

    def choice_field_i(self):
        """
        Выбор поля ID линейных пользователем
        """
        self.dlg.comboBox2_i.clear()
        slayer = self.dlg.comboBox_i.itemData(self.dlg.comboBox_i.currentIndex())
        if slayer is not None:
            [self.dlg.comboBox2_i.addItem(field.name()) for field in slayer.fields()]

    def run(self):
        """
        Запуск основных процессов
        """
        self.dlg = CompilerDialog()
        self.dlg.lineEdit.clear()
        self.dlg.checkBox.setChecked(True)
        self.dlg.toolButton.clicked.connect(self.dct)
        self.dlg.OK.clicked.connect(self.apply)
        self.dlg.Cancel.clicked.connect(self.cancel)
        self.choice_layer()
        self.choice_field()
        self.choice_field_i()
        self.dlg.comboBox.currentIndexChanged.connect(self.choice_field)
        self.dlg.comboBox_i.currentIndexChanged.connect(self.choice_field_i)
        self.dlg.mQgsProjectionSelectionWidget.setCrs(self.instance.crs())
        self.dlg.tabWidget.setCurrentIndex(0)
        self.dlg.show()
        lst = []
        for layer in self.instance.mapLayers().values():
            if layer.type() == QgsMapLayer.VectorLayer:
                lst.append(layer.type())
        if QgsMapLayerType.VectorLayer not in lst:
            error = QMessageBox()
            error.setWindowTitle("Ошибка!")
            error.setText('Проект не содержит векторных слоёв!\n'
                          "Добавьте слои в проект!")
            error.exec_()
            
