"""
Unit tests for AGGREGATE command.
"""

import pytest
import json
from click.testing import CliRunner
from unittest.mock import Mock
import tempfile

from odoo_cli.commands.aggregate import aggregate, parse_domain_string
from odoo_cli.models.context import CliContext


@pytest.fixture
def mock_context():
    """Create mock CLI context"""
    context = Mock(spec=CliContext)
    context.client = Mock()
    context.console = Mock()
    return context


@pytest.fixture
def runner():
    """Create Click test runner"""
    return CliRunner()


class TestParseDomainString:
    """Test domain parsing utility"""

    def test_parse_empty_domain(self):
        """Test parsing empty domain"""
        result = parse_domain_string('[]')
        assert result == []

    def test_parse_simple_domain(self):
        """Test parsing simple domain"""
        result = parse_domain_string('[["name", "=", "Test"]]')
        assert result == [["name", "=", "Test"]]

    def test_parse_complex_domain(self):
        """Test parsing complex domain"""
        result = parse_domain_string('[["state", "=", "sale"], ["amount", ">", 100]]')
        assert len(result) == 2

    def test_parse_invalid_json(self):
        """Test error with invalid JSON"""
        with pytest.raises(ValueError):
            parse_domain_string('{ invalid }')


class TestAggregateCommandSuccess:
    """Test successful AGGREGATE scenarios"""

    def test_aggregate_count(self, runner, mock_context):
        """Test counting records"""
        mock_context.client.search.return_value = [1, 2, 3]
        mock_context.client.read.return_value = [
            {'id': 1, 'name': 'Record 1'},
            {'id': 2, 'name': 'Record 2'},
            {'id': 3, 'name': 'Record 3'},
        ]

        result = runner.invoke(
            aggregate,
            ['sale.order', '[]', '--count'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.search.assert_called_once()

    def test_aggregate_sum(self, runner, mock_context):
        """Test sum aggregation"""
        mock_context.client.search.return_value = [1, 2, 3]
        mock_context.client.read.return_value = [
            {'id': 1, 'amount_total': 100},
            {'id': 2, 'amount_total': 200},
            {'id': 3, 'amount_total': 300},
        ]

        result = runner.invoke(
            aggregate,
            ['sale.order', '[]', '--sum', 'amount_total'],
            obj=mock_context
        )

        assert result.exit_code == 0

    def test_aggregate_avg(self, runner, mock_context):
        """Test average aggregation"""
        mock_context.client.search.return_value = [1, 2, 3, 4]
        mock_context.client.read.return_value = [
            {'id': 1, 'amount_total': 100},
            {'id': 2, 'amount_total': 200},
            {'id': 3, 'amount_total': 300},
            {'id': 4, 'amount_total': 400},
        ]

        result = runner.invoke(
            aggregate,
            ['sale.order', '[]', '--avg', 'amount_total'],
            obj=mock_context
        )

        assert result.exit_code == 0

    def test_aggregate_group_by(self, runner, mock_context):
        """Test grouping by field"""
        mock_context.client.search.return_value = [1, 2, 3]
        mock_context.client.read.return_value = [
            {'id': 1, 'state': 'draft', 'amount_total': 100},
            {'id': 2, 'state': 'sale', 'amount_total': 200},
            {'id': 3, 'state': 'draft', 'amount_total': 300},
        ]

        result = runner.invoke(
            aggregate,
            ['sale.order', '[]', '--sum', 'amount_total', '--group-by', 'state'],
            obj=mock_context
        )

        assert result.exit_code == 0

    def test_aggregate_multiple_fields(self, runner, mock_context):
        """Test aggregating multiple fields"""
        mock_context.client.search.return_value = [1, 2]
        mock_context.client.read.return_value = [
            {'id': 1, 'amount_total': 100, 'amount_untaxed': 80},
            {'id': 2, 'amount_total': 200, 'amount_untaxed': 160},
        ]

        result = runner.invoke(
            aggregate,
            ['sale.order', '[]', '--sum', 'amount_total', '--sum', 'amount_untaxed'],
            obj=mock_context
        )

        assert result.exit_code == 0

    def test_aggregate_json_output(self, runner, mock_context):
        """Test JSON output format"""
        mock_context.client.search.return_value = [1, 2]
        mock_context.client.read.return_value = [
            {'id': 1, 'amount_total': 100},
            {'id': 2, 'amount_total': 200},
        ]

        result = runner.invoke(
            aggregate,
            ['sale.order', '[]', '--sum', 'amount_total', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['success'] is True
        assert 'results' in output
        assert len(output['results']) > 0

    def test_aggregate_custom_batch_size(self, runner, mock_context):
        """Test custom batch size"""
        mock_context.client.search.return_value = list(range(1, 21))
        mock_context.client.read.side_effect = [
            [{'id': i, 'amount_total': i * 100} for i in range(1, 11)],
            [{'id': i, 'amount_total': i * 100} for i in range(11, 21)],
        ]

        result = runner.invoke(
            aggregate,
            ['sale.order', '[]', '--sum', 'amount_total', '--batch-size', '10'],
            obj=mock_context
        )

        assert result.exit_code == 0
        assert mock_context.client.read.call_count == 2


class TestAggregateCommandErrors:
    """Test error handling"""

    def test_invalid_domain(self, runner, mock_context):
        """Test error with invalid domain JSON"""
        result = runner.invoke(
            aggregate,
            ['sale.order', '{ invalid }', '--count'],
            obj=mock_context
        )

        assert result.exit_code == 3

    def test_no_aggregation_specified(self, runner, mock_context):
        """Test error when no aggregation requested"""
        result = runner.invoke(
            aggregate,
            ['sale.order', '[]'],
            obj=mock_context
        )

        assert result.exit_code == 3

    def test_no_records_found(self, runner, mock_context):
        """Test when no records match domain"""
        mock_context.client.search.return_value = []

        result = runner.invoke(
            aggregate,
            ['sale.order', '[["id", "=", 99999]]', '--count'],
            obj=mock_context
        )

        assert result.exit_code == 0  # Should succeed with 0 records

    def test_search_error(self, runner, mock_context):
        """Test error during search"""
        mock_context.client.search.side_effect = Exception("Search failed")

        result = runner.invoke(
            aggregate,
            ['sale.order', '[]', '--count'],
            obj=mock_context
        )

        assert result.exit_code == 3

    def test_read_error(self, runner, mock_context):
        """Test error during read"""
        mock_context.client.search.return_value = [1, 2, 3]
        mock_context.client.read.side_effect = Exception("Read failed")

        result = runner.invoke(
            aggregate,
            ['sale.order', '[]', '--count'],
            obj=mock_context
        )

        assert result.exit_code == 3


class TestAggregateLogic:
    """Test aggregation logic"""

    def test_sum_calculation(self, runner, mock_context):
        """Test sum calculation accuracy"""
        mock_context.client.search.return_value = [1, 2, 3]
        mock_context.client.read.return_value = [
            {'id': 1, 'amount_total': 100.5},
            {'id': 2, 'amount_total': 200.5},
            {'id': 3, 'amount_total': 300.0},
        ]

        result = runner.invoke(
            aggregate,
            ['sale.order', '[]', '--sum', 'amount_total', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['success'] is True
        # Should have 601.0 total
        assert output['results'][0]['amount_total_sum'] == 601.0

    def test_avg_calculation(self, runner, mock_context):
        """Test average calculation accuracy"""
        mock_context.client.search.return_value = [1, 2, 3, 4]
        mock_context.client.read.return_value = [
            {'id': 1, 'amount_total': 100},
            {'id': 2, 'amount_total': 200},
            {'id': 3, 'amount_total': 300},
            {'id': 4, 'amount_total': 400},
        ]

        result = runner.invoke(
            aggregate,
            ['sale.order', '[]', '--avg', 'amount_total', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        # Average should be 250
        assert output['results'][0]['amount_total_avg'] == 250.0

    def test_grouping_accuracy(self, runner, mock_context):
        """Test grouping accuracy"""
        mock_context.client.search.return_value = [1, 2, 3]
        mock_context.client.read.return_value = [
            {'id': 1, 'state': 'draft', 'amount_total': 100},
            {'id': 2, 'state': 'sale', 'amount_total': 200},
            {'id': 3, 'state': 'draft', 'amount_total': 300},
        ]

        result = runner.invoke(
            aggregate,
            ['sale.order', '[]', '--sum', 'amount_total', '--group-by', 'state', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['groups'] == 2  # draft and sale


class TestAggregateOutputFormats:
    """Test output formatting"""

    def test_json_output_structure(self, runner, mock_context):
        """Test JSON output structure"""
        mock_context.client.search.return_value = [1, 2]
        mock_context.client.read.return_value = [
            {'id': 1, 'amount_total': 100},
            {'id': 2, 'amount_total': 200},
        ]

        result = runner.invoke(
            aggregate,
            ['sale.order', '[]', '--count', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert 'success' in output
        assert 'records' in output
        assert 'groups' in output
        assert 'results' in output


class TestAggregateIntegration:
    """Integration tests"""

    def test_full_workflow_count(self, runner, mock_context):
        """Test complete count workflow"""
        mock_context.client.search.return_value = [1, 2, 3, 4, 5]
        mock_context.client.read.return_value = [
            {'id': i} for i in range(1, 6)
        ]

        result = runner.invoke(
            aggregate,
            ['sale.order', '[]', '--count'],
            obj=mock_context
        )

        assert result.exit_code == 0

    def test_full_workflow_sum_and_avg(self, runner, mock_context):
        """Test complete workflow with sum and avg"""
        mock_context.client.search.return_value = [1, 2, 3]
        mock_context.client.read.return_value = [
            {'id': 1, 'amount_total': 100, 'amount_untaxed': 80},
            {'id': 2, 'amount_total': 200, 'amount_untaxed': 160},
            {'id': 3, 'amount_total': 300, 'amount_untaxed': 240},
        ]

        result = runner.invoke(
            aggregate,
            [
                'sale.order', '[]',
                '--sum', 'amount_total',
                '--avg', 'amount_untaxed'
            ],
            obj=mock_context
        )

        assert result.exit_code == 0

    def test_full_workflow_group_and_aggregate(self, runner, mock_context):
        """Test complete workflow with grouping"""
        mock_context.client.search.return_value = [1, 2, 3, 4]
        mock_context.client.read.return_value = [
            {'id': 1, 'state': 'draft', 'amount_total': 100},
            {'id': 2, 'state': 'sale', 'amount_total': 200},
            {'id': 3, 'state': 'draft', 'amount_total': 300},
            {'id': 4, 'state': 'sale', 'amount_total': 400},
        ]

        result = runner.invoke(
            aggregate,
            [
                'sale.order', '[]',
                '--count',
                '--sum', 'amount_total',
                '--group-by', 'state'
            ],
            obj=mock_context
        )

        assert result.exit_code == 0
