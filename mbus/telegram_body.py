import json

from dif_telegram_field import DIFTelegramField, DIFETelegramField
from vif_telegram_field import VIFTelegramField, VIFETelegramField

from telegram_field import TelegramField
from telegram_data_field import TelegramDataField
from telegram_variable_data_record import TelegramVariableDataRecord


class TelegramBodyPayload(object):
    def __init__(self, payload=None):
        self._bodyField = TelegramField()
        if payload is not None:
            self._bodyField = TelegramField(payload)

        self._records = []

    @property
    def records(self):
        return self._records

    @records.setter
    def records(self, value):
        self._records = value

    @property
    def bodyField(self):
        return self._bodyField

    @bodyField.setter
    def bodyField(self, value):
        self._bodyField = TelegramField(value)

    def createTelegramBodyPayload(self, payload):
        self.bodyField = payload

    def setTelegramBodyPayload(self, payload):
        self.bodyField = payload

    def parse(self):
        self.records = []

        recordPos = 0

        try:
            while recordPos < len(self.bodyField.field_parts):
                recordPos = self._parseVariableDataRecord(recordPos)
        except IndexError:
            print "UserDATA runaway -----------------------------------"

    def _parseVariableDataRecord(self, startPos):
        lowerBoundary = 0
        upperBoundary = 0
        lvarBit = False

        rec = TelegramVariableDataRecord()
        dif = DIFTelegramField()
        dif.field_parts.append(self.bodyField.field_parts[startPos])
        dif.parse()

        rec.dif = dif

        if dif.is_end_of_user_data:
            # only manufacturer specific data left, stop parsing
            return len(self.bodyField.field_parts)

        difeList = []
        if dif.is_extension_bit:
            difeList = self._parseDIFEFIelds(startPos + 1)

        rec.difes += difeList

        # Increase startPos by 1 (DIF) and the count of DIFEs
        vif = VIFTelegramField()
        vif.field_parts.append(
            self.bodyField.field_parts[startPos + 1 + len(difeList)])
        vif.parent = rec
        vif.parse()

        rec.vif = vif

        vifeList = []

        if vif.is_extension_bit:
            # increase startPosition by 2 (DIF and VIF) and the number of DIFEs
            vifeList = self._parseVIFEFields(startPos + 2 + len(difeList), rec)
            # check if there exist a LVAR Byte at the beginning of the data
            # field
            lvarBit = vifeList[0].is_lvar_bit

        rec.vifes += vifeList

        lowerBoundary = startPos + 2 + len(difeList) + len(vifeList)

        # if there exist a LVAR Byte at the beginning of the data field,
        # change the data field length
        if lvarBit:
            dif.data_field_length = self.bodyField.field_parts[lowerBoundary]
            lowerBoundary += 1

        upperBoundary = lowerBoundary + dif.data_field_length

        if dif.data_field_length == 0:
            return upperBoundary

        if len(self.bodyField.field_parts) >= upperBoundary:
            dataField = TelegramDataField(rec)
            dataField.field_parts += \
                self.bodyField.field_parts[lowerBoundary:upperBoundary]
            dataField.parse()
            rec.dataField = dataField

        self.records.append(rec)

        print "POS -------------- ", upperBoundary
        print "ADDED RECORD-------------------------", len(self.records)

        return upperBoundary

    def _parseDIFEFields(self, pos):
        difeList = []
        extension_bit_set = True
        dife = None

        while extensionBitSet:
            if len(self.bodyField.field_parts) < pos:
                # TODO: Throw Exception
                pass

            dife = self._processSingleDIFEField(self.bodyField.field_parts[pos])
            difeList.append(dife)
            extension_bit_set = dife.is_extension_bit
            pos += 1

        return difeList

    def _parseVIFEFields(self, position, parent):
        vifeList = []
        extension_bit_set = True
        vife = None

        while extension_bit_set:
            if len(self.bodyField.field_parts) < position:
                # TODO: throw exception
                pass

            vife = self._processSingleVIFEField(self.bodyField.field_parts[position], parent)
            vifeList.append(vife)
            extension_bit_set = vife.is_extension_bit
            position += 1

        return vifeList

    def _processSingleDIFEField(self, field_value):
        dife = DIFETelegramField()
        dife.field_parts += field_value
        return dife

    def _processSingleVIFEField(self, field_value, parent):
        vife = VIFETelegramField()
        vife.field_parts.append(field_value)
        vife.parent = parent
        vife.parse()
        return vife

    def debug(self):
        print "-------------------------------------------------------------"
        print "-------------------- BEGIN BODY PAYLOAD ---------------------"
        print "-------------------------------------------------------------"

        if self.records:
            for index, record in enumerate(self.records):
                print "RECORD:", index 
                record.debug()
        print "-------------------------------------------------------------"
        print "--------------------- END BODY PAYLOAD ----------------------"
        print "-------------------------------------------------------------"


class TelegramBodyHeader(object):
    def __init__(self):
        self._ci_field = TelegramField()        # control information field
        self._id_nr_field = TelegramField()     # identification number field
        self._manufacturer_field = TelegramField()     # manufacturer
        self._version_field = TelegramField()          # version
        self._measure_medium_field = TelegramField()   # measured medium
        self._acc_nr_field = TelegramField()           # access number
        self._status_field = TelegramField()           # status
        self._sig_field = TelegramField()              # signature field

    def createTelegramBodyHeader(self, bodyHeader):
        self.ci_field = bodyHeader[0]
        self.id_nr_field = bodyHeader[1:5]
        self.manufacturer_field = bodyHeader[5:7]
        self.version_field = bodyHeader[7]
        self.measure_medium_field = bodyHeader[8]
        self.acc_nr_field = bodyHeader[9]
        self.status_field = bodyHeader[10]
        self.sig_field = bodyHeader[11:13]

    @property
    def id_nr(self):
        """ID number of telegram in reverse byte order"""
        return self._id_nr_field[::-1]

    @property
    def ci_field(self):
        return self._ci_field

    @ci_field.setter
    def ci_field(self, value):
        self._ci_field = TelegramField(value)

    @property
    def id_nr_field(self):
        return self._id_nr_field

    @id_nr_field.setter
    def id_nr_field(self, value):
        self._id_nr_field = TelegramField(value)

    @property
    def manufacturer_field(self):
        return self._manufacturer_field

    @manufacturer_field.setter
    def manufacturer_field(self, value):
        self._manufacturer_field = TelegramField(value)

    @property
    def version_field(self):
        return self._version_field

    @version_field.setter
    def version_field(self, value):
        self._version_field = TelegramField(value)

    @property
    def measure_medium_field(self):
        return self._measure_medium_field

    @measure_medium_field.setter
    def measure_medium_field(self, value):
        self._measure_medium_field = TelegramField(value)

    @property
    def acc_nr_field(self):
        return self._acc_nr_field

    @acc_nr_field.setter
    def acc_nr_field(self, value):
        self._acc_nr_field = TelegramField(value)

    @property
    def status_field(self):
        return self._status_field

    @status_field.setter
    def status_field(self, value):
        self._status_field = TelegramField(value)

    @property
    def sig_field(self):
        return self._sig_field

    @sig_field.setter
    def sig_field(self, value):
        self._sig_field = TelegramField(value)

    def debug(self):
        print "DEBUG DISABLED", self
        return

        print "Type of TelegramBodyHeader:".ljust(30), 	hex(self.ciField.field_parts[0])
        print "Identification#:".ljust(30),				", ".join(map(hex, self.id_nr))
        print "Manufacturer:".ljust(30), self.manufacturer_field.decodeManufacturer
        print "Version:".ljust(30),						hex(self.vField.field_parts[0])
        print "Medium:".ljust(30),						hex(self.medField.field_parts[0])
        print "StatusField:".ljust(30),					hex(self.statusField.field_parts[0])
        print "Sig-Fields:".ljust(30),					", ".join(map(hex, self.sigField.field_parts)) # FIX PARSE

    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class TelegramBody(object):
    def __init__(self):
        self._bodyHeader       = TelegramBodyHeader()
        self._bodyPayload      = TelegramBodyPayload()
        self._bodyHeaderLength = 13

    @property
    def bodyHeaderLength(self):
        return self._bodyHeaderLength

    @property
    def bodyHeader(self):
        return self._bodyHeader

    @bodyHeader.setter
    def bodyHeader(self, val):
        self._bodyHeader = TelegramBodyHeader()
        self._bodyHeader.createTelegramBodyHeader(val[0:self.bodyHeaderLength])

    @property
    def bodyPayload(self):
        return self._bodyPayload

    @bodyPayload.setter
    def bodyPayload(self, val):
        self._bodyPayload = TelegramBodyPayload(val)

    def createTelegramBody(self, body):
        self.bodyHeader = body[0:self.bodyHeaderLength]
        self.bodyPayload.createTelegramBodyPayload(body[self.bodyHeaderLength:])

    def parse(self):
        self.bodyPayload.parse() # Load from raw into records

    def debug(self):
        self.bodyHeader.debug()
        self.bodyPayload.debug()