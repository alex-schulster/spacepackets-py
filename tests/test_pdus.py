from unittest import TestCase
from spacepackets.cfdp.pdu.ack import AckPdu, ConditionCode, DirectiveCodes, TransactionStatus, \
    CrcFlag
from spacepackets.cfdp.conf import PduConfig, TransmissionModes, Direction, FileSize
from spacepackets.cfdp.pdu.nak import NakPdu
from spacepackets.cfdp.pdu.finished import FinishedPdu, DeliveryCode, FileDeliveryStatus
from spacepackets.cfdp.tlv import CfdpTlv, TlvTypes, FileStoreResponseTlv, FilestoreActionCode, \
    FilestoreResponseStatusCode, EntityIdTlv
from spacepackets.util import get_printable_data_string, PrintFormats


class TestPdus(TestCase):

    def test_ack_pdu(self):
        pdu_conf = PduConfig(
            transaction_seq_num=bytes([0x00, 0x01]),
            source_entity_id=bytes([0x00, 0x00]),
            dest_entity_id=bytes([0x00, 0x01]),
            crc_flag=CrcFlag.NO_CRC,
            trans_mode=TransmissionModes.ACKNOWLEDGED
        )
        ack_pdu = AckPdu(
            directive_code_of_acked_pdu=DirectiveCodes.FINISHED_PDU,
            condition_code_of_acked_pdu=ConditionCode.NO_ERROR,
            transaction_status=TransactionStatus.TERMINATED,
            pdu_conf=pdu_conf
        )
        self.check_fields_packet_0(ack_pdu=ack_pdu)
        ack_pdu_raw = ack_pdu.pack()
        self.assertEqual(len(ack_pdu_raw), 13)
        self.assertEqual(
            ack_pdu_raw,
            # 0x06 because this is the directive code of ACK PDUs
            # 0x51 because 0x05 << 4 is the directive code of the Finished PDU and 0b0001 because
            # because this is the value of finished PDUs
            # 0x02 because this is the terminated transaction status
            bytes([0x20, 0x00, 0x03, 0x22, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x06, 0x51, 0x02])
        )
        ack_pdu_unpacked = AckPdu.unpack(raw_packet=ack_pdu_raw)
        self.check_fields_packet_0(ack_pdu=ack_pdu_unpacked)

        pdu_conf = PduConfig(
            transaction_seq_num=bytes([0x50, 0x00, 0x10, 0x01]),
            source_entity_id=bytes([0x10, 0x00, 0x01, 0x02]),
            dest_entity_id=bytes([0x30, 0x00, 0x01, 0x03]),
            crc_flag=CrcFlag.WITH_CRC,
            trans_mode=TransmissionModes.UNACKNOWLEDGED
        )
        ack_pdu_2 = AckPdu(
            directive_code_of_acked_pdu=DirectiveCodes.EOF_PDU,
            condition_code_of_acked_pdu=ConditionCode.POSITIVE_ACK_LIMIT_REACHED,
            transaction_status=TransactionStatus.ACTIVE,
            pdu_conf=pdu_conf
        )
        self.check_fields_packet_1(ack_pdu=ack_pdu_2)
        ack_pdu_raw = ack_pdu_2.pack()
        self.assertEqual(len(ack_pdu_raw), 19)
        self.assertEqual(
            ack_pdu_raw,
            # 0x06 because this is the directive code of ACK PDUs
            # 0x40 because 0x04 << 4 is the directive code of the EOF PDU and 0b0000 because
            # because this is not a Finished PDUs
            # 0x11 because this has the Active transaction status and the condition code is the
            # Positive Ack Limit Reached Condition Code
            bytes([
                0x26, 0x00, 0x03, 0x44,
                0x10, 0x00, 0x01, 0x02,
                0x50, 0x00, 0x10, 0x01,
                0x30, 0x00, 0x01, 0x03,
                0x06, 0x40, 0x11
            ])
        )
        # Invalid directive code
        pdu_conf = PduConfig.empty()
        self.assertRaises(
            ValueError, AckPdu,
            directive_code_of_acked_pdu=DirectiveCodes.NAK_PDU,
            condition_code_of_acked_pdu=ConditionCode.POSITIVE_ACK_LIMIT_REACHED,
            transaction_status=TransactionStatus.ACTIVE,
            pdu_conf=pdu_conf
        )

    def check_fields_packet_0(self, ack_pdu: AckPdu):
        self.assertEqual(ack_pdu.directive_code_of_acked_pdu, DirectiveCodes.FINISHED_PDU)
        self.assertEqual(ack_pdu.condition_code_of_acked_pdu, ConditionCode.NO_ERROR)
        self.assertEqual(ack_pdu.transaction_status, TransactionStatus.TERMINATED)
        self.assertEqual(
            ack_pdu.pdu_file_directive.pdu_header.pdu_conf.transaction_seq_num, bytes([0x00, 0x01])
        )
        self.assertEqual(
            ack_pdu.pdu_file_directive.pdu_header.pdu_conf.source_entity_id, bytes([0x00, 0x00])
        )
        self.assertEqual(
            ack_pdu.pdu_file_directive.pdu_header.pdu_conf.dest_entity_id, bytes([0x00, 0x01])
        )
        self.assertEqual(
            ack_pdu.pdu_file_directive.pdu_header.pdu_conf.trans_mode,
            TransmissionModes.ACKNOWLEDGED
        )
        self.assertEqual(ack_pdu.packet_len, 13)

    def check_fields_packet_1(self, ack_pdu: AckPdu):
        self.assertEqual(ack_pdu.directive_code_of_acked_pdu, DirectiveCodes.EOF_PDU)
        self.assertEqual(
            ack_pdu.condition_code_of_acked_pdu, ConditionCode.POSITIVE_ACK_LIMIT_REACHED
        )
        self.assertEqual(ack_pdu.transaction_status, TransactionStatus.ACTIVE)
        self.assertEqual(
            ack_pdu.pdu_file_directive.pdu_header.transaction_seq_num,
            bytes([0x50, 0x00, 0x10, 0x01])
        )
        self.assertEqual(
            ack_pdu.pdu_file_directive.pdu_header.pdu_conf.source_entity_id,
            bytes([0x10, 0x00, 0x01, 0x02])
        )
        self.assertEqual(
            ack_pdu.pdu_file_directive.pdu_header.pdu_conf.dest_entity_id,
            bytes([0x30, 0x00, 0x01, 0x03])
        )
        self.assertEqual(
            ack_pdu.pdu_file_directive.pdu_header.pdu_conf.trans_mode,
            TransmissionModes.UNACKNOWLEDGED
        )
        self.assertEqual(ack_pdu.packet_len, 19)

    def test_nak_pdu(self):
        pdu_conf = PduConfig(
            trans_mode=TransmissionModes.ACKNOWLEDGED,
            transaction_seq_num=bytes([0x00, 0x01]),
            source_entity_id=bytes([0x00, 0x00]),
            dest_entity_id=bytes([0x00, 0x01])
        )
        nak_pdu = NakPdu(
            start_of_scope=0,
            end_of_scope=200,
            pdu_conf=pdu_conf
        )
        self.assertEqual(nak_pdu.segment_requests, [])
        pdu_header = nak_pdu.pdu_file_directive.pdu_header
        self.assertEqual(pdu_header.direction, Direction.TOWARDS_RECEIVER)
        # Start of scope (4) + end of scope (4) + directive code
        self.assertEqual(pdu_header.pdu_data_field_len, 8 + 1)
        self.assertEqual(pdu_header.file_size, FileSize.NORMAL)
        self.assertEqual(pdu_header.trans_mode, TransmissionModes.ACKNOWLEDGED)
        self.assertEqual(nak_pdu.file_size, FileSize.NORMAL)
        self.assertEqual(nak_pdu.packet_len, 19)
        nak_packed = nak_pdu.pack()
        self.assertEqual(len(nak_packed), 19)
        nak_pdu.file_size = FileSize.LARGE
        self.assertEqual(pdu_header.file_size, FileSize.LARGE)
        self.assertEqual(nak_pdu.file_size, FileSize.LARGE)
        self.assertEqual(nak_pdu.packet_len, 27)
        nak_packed = nak_pdu.pack()
        self.assertEqual(len(nak_packed), 27)

        nak_pdu.file_size = FileSize.NORMAL
        self.assertEqual(pdu_header.file_size, FileSize.NORMAL)
        self.assertEqual(nak_pdu.file_size, FileSize.NORMAL)
        self.assertEqual(nak_pdu.packet_len, 19)
        nak_packed = nak_pdu.pack()
        self.assertEqual(len(nak_packed), 19)

        nak_pdu.start_of_scope = pow(2, 32) + 1
        nak_pdu.end_of_scope = pow(2, 32) + 1
        self.assertRaises(ValueError, nak_pdu.pack)

        nak_pdu.start_of_scope = 0
        nak_pdu.end_of_scope = 200
        segment_requests = [(20, 40), (60, 80)]
        nak_pdu.segment_requests = segment_requests
        self.assertEqual(nak_pdu.segment_requests, segment_requests)
        # Additional 2 segment requests, each has size 8
        self.assertEqual(nak_pdu.packet_len, 35)
        nak_packed = nak_pdu.pack()
        self.assertEqual(len(nak_packed), 35)
        nak_unpacked = NakPdu.unpack(raw_packet=nak_packed)
        self.assertEqual(nak_unpacked.pack(), nak_packed)

        nak_pdu.file_size = FileSize.LARGE
        # 2 segment requests with size 16 each plus 16 for start and end of scope
        self.assertEqual(nak_pdu.pdu_file_directive.pdu_header.header_len, 10)
        self.assertEqual(nak_pdu.pdu_file_directive.header_len, 11)
        self.assertEqual(nak_pdu.packet_len, 11 + 48)
        nak_packed = nak_pdu.pack()
        self.assertEqual(len(nak_packed), 59)
        nak_repacked = nak_unpacked.pack()
        nak_unpacked = NakPdu.unpack(raw_packet=nak_packed)
        self.assertEqual(nak_unpacked.pack(), nak_packed)
        nak_repacked.append(0)
        self.assertRaises(ValueError, NakPdu.unpack, raw_packet=nak_repacked)
        nak_pdu.segment_requests = []
        self.assertEqual(nak_pdu.packet_len, 59 - 32)
        nak_packed = nak_pdu.pack()
        self.assertEqual(len(nak_packed), 59 - 32)

        nak_pdu.file_size = FileSize.NORMAL
        segment_requests = [(pow(2, 32) + 1, 40), (60, 80)]
        nak_pdu.segment_requests = segment_requests
        self.assertRaises(ValueError, nak_pdu.pack)

    def test_finished_pdu(self):
        pdu_conf = PduConfig.empty()
        finish_pdu = FinishedPdu(
            delivery_code=DeliveryCode.DATA_COMPLETE,
            file_delivery_status=FileDeliveryStatus.FILE_STATUS_UNREPORTED,
            condition_code=ConditionCode.NO_ERROR,
            pdu_conf=pdu_conf
        )
        self.assertEqual(finish_pdu.delivery_code, DeliveryCode.DATA_COMPLETE)
        self.assertEqual(
            finish_pdu.file_delivery_status, FileDeliveryStatus.FILE_STATUS_UNREPORTED
        )
        self.assertEqual(finish_pdu.pdu_file_directive.packet_len, 9)
        finish_pdu_raw = finish_pdu.pack()
        self.assertEqual(len(finish_pdu_raw), 9)
        # 0x02 because the only parameters is the 0x05 directive code and the 0x03 from the file
        # delivery status
        self.assertEqual(
            finish_pdu_raw, bytes([0x20, 0x00, 0x02, 0x11, 0x00, 0x00, 0x00, 0x05, 0x03])
        )
        finish_pdu_unpacked = FinishedPdu.unpack(raw_packet=finish_pdu_raw)
        self.assertEqual(finish_pdu_unpacked.delivery_code, DeliveryCode.DATA_COMPLETE)
        self.assertEqual(
            finish_pdu_unpacked.file_delivery_status, FileDeliveryStatus.FILE_STATUS_UNREPORTED
        )
        self.assertEqual(finish_pdu_unpacked.pdu_file_directive.packet_len, 9)
        finish_pdu_repacked = finish_pdu_unpacked.pack()
        self.assertEqual(finish_pdu.pdu_file_directive.packet_len, 9)
        self.assertEqual(finish_pdu_repacked, finish_pdu_raw)
        finish_pdu_repacked = finish_pdu_repacked[:-1]
        self.assertRaises(ValueError, FinishedPdu.unpack, raw_packet=finish_pdu_repacked)

        # Now generate a packet with a fault location
        fault_location_tlv = EntityIdTlv(
            entity_id=bytes([0x00, 0x02])
        )
        self.assertEqual(fault_location_tlv.packet_len, 4)
        finish_pdu_with_fault_loc = FinishedPdu(
            delivery_code=DeliveryCode.DATA_INCOMPLETE,
            file_delivery_status=FileDeliveryStatus.DISCARDED_DELIBERATELY,
            condition_code=ConditionCode.POSITIVE_ACK_LIMIT_REACHED,
            fault_location=fault_location_tlv,
            pdu_conf=pdu_conf
        )
        self.assertEqual(finish_pdu_with_fault_loc.delivery_code, DeliveryCode.DATA_INCOMPLETE)
        self.assertEqual(
            finish_pdu_with_fault_loc.file_delivery_status,
            FileDeliveryStatus.DISCARDED_DELIBERATELY
        )
        self.assertEqual(
            finish_pdu_with_fault_loc.condition_code, ConditionCode.POSITIVE_ACK_LIMIT_REACHED
        )
        self.assertEqual(finish_pdu_with_fault_loc.fault_location, fault_location_tlv)
        # 4 additional bytes because the entity ID in the TLV has 2 bytes
        self.assertEqual(finish_pdu_with_fault_loc.packet_len, 13)
        self.assertEqual(len(finish_pdu_with_fault_loc.pack()), 13)
        self.assertEqual(finish_pdu_with_fault_loc.fault_location_len, 4)

        # Now create a packet with filestore responses
        filestore_reponse_1 = FileStoreResponseTlv(
            action_code=FilestoreActionCode.REMOVE_DIR_SNN,
            first_file_name="test.txt",
            status_code=FilestoreResponseStatusCode.REMOVE_DIR_SUCCESS
        )
        filestore_response_1_packed = filestore_reponse_1.pack()
        self.assertEqual(
            filestore_response_1_packed,
            bytes([
                TlvTypes.FILESTORE_RESPONSE, 11, 0x60, 0x08, 0x74, 0x65, 0x73, 0x74, 0x2e,
                0x74, 0x78, 0x74, 0x00
            ])
        )
        self.assertEqual(filestore_reponse_1.packet_len, 13)
        pdu_with_response = FinishedPdu(
            delivery_code=DeliveryCode.DATA_INCOMPLETE,
            file_delivery_status=FileDeliveryStatus.DISCARDED_DELIBERATELY,
            condition_code=ConditionCode.FILESTORE_REJECTION,
            pdu_conf=pdu_conf,
            file_store_responses=[filestore_reponse_1]
        )
        self.assertEqual(pdu_with_response.packet_len, 22)
        pdu_with_response_raw = pdu_with_response.pack()
        expected_array = bytearray([
            0x20, 0x00, 0x0f, 0x11, 0x00, 0x00, 0x00, 0x05, 0x44
        ])
        expected_array.extend(filestore_response_1_packed)
        self.assertEqual(expected_array, pdu_with_response_raw)
        pdu_with_response_unpacked = FinishedPdu.unpack(raw_packet=pdu_with_response_raw)
        self.assertEqual(len(pdu_with_response_unpacked.file_store_responses), 1)

        # Pack with 2 responses and 1 fault location
        first_file = 'test.txt'
        second_file = 'test2.txt'
        filestore_reponse_2 = FileStoreResponseTlv(
            action_code=FilestoreActionCode.APPEND_FILE_SNP,
            first_file_name=first_file,
            second_file_name=second_file,
            status_code=FilestoreResponseStatusCode.APPEND_NOT_PERFORMED
        )
        fs_response_2_raw = filestore_reponse_2.pack()
        expected_reply = bytearray()
        expected_reply.extend(bytes([0x01, 0x15, 0x3f]))
        expected_reply.append(len(first_file))
        expected_reply.extend(first_file.encode())
        expected_reply.append(len(second_file))
        expected_reply.extend(second_file.encode())
        # 0 length filestore message
        expected_reply.append(0)
        self.assertEqual(filestore_reponse_2.packet_len, 23)
        self.assertEqual(fs_response_2_raw, expected_reply)
        finish_pdu_two_responses_one_fault_loc = FinishedPdu(
            delivery_code=DeliveryCode.DATA_COMPLETE,
            file_delivery_status=FileDeliveryStatus.FILE_RETAINED,
            condition_code=ConditionCode.CHECK_LIMIT_REACHED,
            pdu_conf=pdu_conf,
            file_store_responses=[filestore_reponse_1, filestore_reponse_2],
            fault_location=fault_location_tlv
        )
        # length should be 13 (response 1) + 23 (response 2)  + 4 (fault loc) + 9 (base)
        self.assertEqual(finish_pdu_two_responses_one_fault_loc.packet_len, 49)
        fs_responses = finish_pdu_two_responses_one_fault_loc.file_store_responses
        self.assertEqual(len(fs_responses), 2)
        complex_pdu_raw = finish_pdu_two_responses_one_fault_loc.pack()
        complex_pdu_unpacked = FinishedPdu.unpack(raw_packet=complex_pdu_raw)
        self.assertEqual(complex_pdu_unpacked.fault_location.pack(), fault_location_tlv.pack())
        self.assertEqual(filestore_reponse_1.pack(), fs_responses[0].pack())
        self.assertEqual(filestore_reponse_2.pack(), fs_responses[1].pack())

        # Change TLV type to make it invalid
        complex_pdu_raw[-5] = TlvTypes.FILESTORE_RESPONSE
        with self.assertRaises(ValueError):
            FinishedPdu.unpack(raw_packet=complex_pdu_raw)

    def test_keep_alive_pdu(self):
        pass

    def test_metadata_pdu(self):
        pass

    def test_prompt_pdu(self):
        pass
