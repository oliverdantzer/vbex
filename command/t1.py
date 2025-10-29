from bvex_codec.sample import Sample, SampleMetadata, PrimitiveData, WhichDataType

metadata = SampleMetadata(
    metric_id="test_metric",
    timestamp=1234567890.0,
    which_data_type=WhichDataType.PRIMITIVE,
)
data = PrimitiveData.from_value(42)
sample = Sample(metadata=metadata, data=data)
print(sample.model_dump_json())
