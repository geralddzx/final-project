/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

//My includes
#include "include/headers.p4"
#include "include/parsers.p4"

#define INDEX_SIZE 4096
#define NORMAL 0
#define CLONE 2
#define RECIRC 4

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}

/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    register<fid>(INDEX_SIZE) fids;

    action drop() {
        mark_to_drop();
    }

    action ecmp_group(bit<14> ecmp_group_id, bit<16> num_nhops){
        findex index;
        hash(index,
            HashAlgorithm.crc16,
            (bit<1>)0,
            { hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr,
              hdr.ipv4.protocol,
              hdr.tcp.srcPort,
              hdr.tcp.dstPort },
            (bit<16>)INDEX_SIZE);
        fid id;
        fids.read(id, index);

        hash(meta.ecmp_hash,
	    HashAlgorithm.crc16,
	    (bit<1>)0,
	    { hdr.ipv4.srcAddr,
	      hdr.ipv4.dstAddr,
          id,
          hdr.tcp.srcPort,
          hdr.tcp.dstPort,
          hdr.ipv4.protocol},
	    num_nhops);

	    meta.ecmp_group_id = ecmp_group_id;
    }

    action set_nhop(macAddr_t dstAddr, egressSpec_t port) {

        //set the src mac address as the previous dst, this is not correct right?
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;

       //set the destination mac address that we got from the match in the table
        hdr.ethernet.dstAddr = dstAddr;

        //set the output port that we also get from the table
        standard_metadata.egress_spec = port;

        //decrease ttl by 1
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    action set_node_type(bit<14> node_type) {
        meta.node_type = node_type;
    }

    table ecmp_group_to_nhop {
        key = {
            meta.ecmp_group_id:    exact;
            meta.ecmp_hash: exact;
        }
        actions = {
            drop;
            set_nhop;
        }
        size = 1024;
    }

    table egress_type {
        key = {
            standard_metadata.egress_spec: exact;
        }
        actions = {
            set_node_type;
        }
        size = 16;
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            set_nhop;
            ecmp_group;
            drop;
        }
        size = 1024;
        default_action = drop;
    }

    apply {
        if (hdr.ipv4.isValid()){
            switch (ipv4_lpm.apply().action_run){
                ecmp_group: {
                    ecmp_group_to_nhop.apply();
                }
            }
            egress_type.apply();

            if (meta.node_type == 1 && hdr.notification.isValid()) {
                fid new_id;
                random(new_id, (fid)0, (fid)65535);

                findex index;
                hash(index,
                    HashAlgorithm.crc16,
                    (bit<1>)0,
                    { hdr.ipv4.dstAddr,
                      hdr.ipv4.srcAddr,
                      hdr.ipv4.protocol,
                      hdr.tcp.srcPort,
                      hdr.tcp.dstPort },
                    (bit<16>)INDEX_SIZE);

                fids.write(index, new_id);
                mark_to_drop();
            }
        }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {

    register<ftimestamp>(INDEX_SIZE) ftimestamps;
    register<frand>(INDEX_SIZE) frands;

    apply {
        if (standard_metadata.instance_type == CLONE) {
            ip4Addr_t srcAddr = hdr.ipv4.srcAddr;
            hdr.ipv4.srcAddr = hdr.ipv4.dstAddr;
            hdr.ipv4.dstAddr = srcAddr;
            hdr.telemetry.setInvalid();
            hdr.notification.setValid();
            hdr.notification.nextHeaderType = TYPE_IPV4;
            hdr.ethernet.etherType = TYPE_NOTIFICATION;
            recirculate(meta.feedback);
        } else {
            if (!hdr.notification.isValid()) {
                if (hdr.telemetry.isValid()) {
                    if ((bit<16>)standard_metadata.enq_qdepth > hdr.telemetry.enq_qdepth) {
                        hdr.telemetry.enq_qdepth = (bit<16>)standard_metadata.enq_qdepth;
                    }
                } else {
                    hdr.ethernet.etherType = TYPE_TELEMETRY;
                    hdr.telemetry.setValid();
                    hdr.telemetry.enq_qdepth = (bit<16>)standard_metadata.enq_qdepth;
                    hdr.telemetry.nextHeaderType = TYPE_IPV4;
                }

                if (hdr.telemetry.enq_qdepth > 32) {
                    findex index;
                    hash(index,
                	    HashAlgorithm.crc16,
                	    (bit<1>)0,
                	    { hdr.ipv4.srcAddr,
                	      hdr.ipv4.dstAddr,
                          hdr.ipv4.protocol,
                          hdr.tcp.srcPort,
                          hdr.tcp.dstPort },
                	    (bit<16>)INDEX_SIZE);

                    ftimestamp tstamp;
                    ftimestamps.read(tstamp, index);

                    if (standard_metadata.ingress_global_timestamp - tstamp > 50000) {
                        ftimestamps.write(index, standard_metadata.ingress_global_timestamp);
                        frand rand;
                        frands.read(rand, index);
                        frand randint;
                        random(randint, (frand)0, rand);
                        if (randint == 0) {
                            clone(CloneType.E2E, 100);
                            frands.write(index, rand + 1);
                        }
                    }
                }

                if (meta.node_type == 1) {
                    hdr.telemetry.setInvalid();
                    hdr.ethernet.etherType = TYPE_IPV4;
                }
            }
        }
    }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
     apply {
	update_checksum(
	    hdr.ipv4.isValid(),
            { hdr.ipv4.version,
	          hdr.ipv4.ihl,
              hdr.ipv4.dscp,
              hdr.ipv4.ecn,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
              hdr.ipv4.hdrChecksum,
              HashAlgorithm.csum16);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

//switch architecture
V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
